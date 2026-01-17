from datetime import datetime
from uuid import UUID
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.models import Project, ProjectStatus, ProjectStatusHistory, User, UserRole

class LifecycleService:
    """
    Manages the Deal Pipeline Lifecycle logic, enforcing transition rules
    and recording status history.
    """

    TRANSITION_RULES = {
        # Format: (FromStatus, ToStatus): {
        #   "allowed_roles": [list of UserRole], 
        #   "min_score": float (optional),
        #   "requires_docs": [list of doc types] (optional),
        #   "auto": bool (is mostly automated)
        # }
        
        # 1. Draft -> Pipeline
        (ProjectStatus.DRAFT, ProjectStatus.PIPELINE): {
            "allowed_roles": [UserRole.TWG_FACILITATOR, UserRole.ADMIN, UserRole.SECRETARIAT_LEAD],
            "auto": False
        },
        
        # 2. Pipeline -> Under Review (Automated when scoring starts)
        (ProjectStatus.PIPELINE, ProjectStatus.UNDER_REVIEW): {
            "allowed_roles": [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD], # and System (automated)
            "auto": True
        },
        
        # 3. Under Review -> [Decisions] (Automated based on score)
        (ProjectStatus.UNDER_REVIEW, ProjectStatus.DECLINED): {
            "allowed_roles": [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD],
            "auto": True # Score < 5.0
        },
        (ProjectStatus.UNDER_REVIEW, ProjectStatus.NEEDS_REVISION): {
            "allowed_roles": [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD],
            "auto": True # Score 5.0 - 7.4
        },
        (ProjectStatus.UNDER_REVIEW, ProjectStatus.SUMMIT_READY): {
            "allowed_roles": [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD],
            "min_score": 7.5,
            "auto": True # Score >= 7.5
        },

        # 4. Resubmission Loop
        (ProjectStatus.NEEDS_REVISION, ProjectStatus.UNDER_REVIEW): {
             "allowed_roles": [UserRole.TWG_FACILITATOR, UserRole.ADMIN, UserRole.SECRETARIAT_LEAD],
             "auto": False
        },
        
        # 5. Deal Room Entry
        (ProjectStatus.SUMMIT_READY, ProjectStatus.DEAL_ROOM_FEATURED): {
            "allowed_roles": [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD],
            "auto": False # Curation is manual/algorithm assisted but final approval manual
        },
        
        # 6. Negotiation
        (ProjectStatus.SUMMIT_READY, ProjectStatus.IN_NEGOTIATION): {
             "allowed_roles": [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD],
             "auto": False
        },
        (ProjectStatus.DEAL_ROOM_FEATURED, ProjectStatus.IN_NEGOTIATION): {
             "allowed_roles": [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD],
             "auto": False
        },
        
        # 7. Commitment
        (ProjectStatus.IN_NEGOTIATION, ProjectStatus.COMMITTED): {
            "allowed_roles": [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD],
            "auto": False
        },
        
        # 8. Post-Deal
        (ProjectStatus.COMMITTED, ProjectStatus.IMPLEMENTED): {
             "allowed_roles": [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD],
             "auto": False
        },
        
        # 9. Generic Archive/Hold (from any active state mostly)
        # We handle these somewhat generically logic-side if needed, or explicit rules
    }

    STAGE_DURATION_THRESHOLDS = {
        ProjectStatus.DRAFT: 14,
        ProjectStatus.PIPELINE: 7,
        ProjectStatus.UNDER_REVIEW: 14,
        ProjectStatus.NEEDS_REVISION: 14,
        ProjectStatus.SUMMIT_READY: 30,
        ProjectStatus.DEAL_ROOM_FEATURED: 30,
        ProjectStatus.IN_NEGOTIATION: 60,
        ProjectStatus.COMMITTED: 90,
    }

    @staticmethod
    def get_allowed_transitions(current_status: ProjectStatus, role: Optional[UserRole] = None) -> List[str]:
        """
        Get list of allowed next statuses.
        """
        allowed = []
        for (src, dst), rule in LifecycleService.TRANSITION_RULES.items():
            if src == current_status:
                if role:
                    if role in rule["allowed_roles"] or role == UserRole.ADMIN:
                        allowed.append(dst.value)
                else:
                    # If no role specified, return all possible
                    allowed.append(dst.value)
        
        # Add generics if appropriate (simplification)
        return allowed


    @staticmethod
    async def transition_project_status(
        db: AsyncSession,
        project_id: UUID,
        new_status: ProjectStatus,
        changed_by_user: User,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        is_automated: bool = False
    ) -> Project:
        """
        Transitions a project to a new status if rules are met.
        """
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalars().first()
        
        if not project:
             raise HTTPException(status_code=404, detail="Project not found")

        current_status = project.status
        
        # 1. Check if change is actual
        if current_status == new_status:
            return project

        # 2. Check Transition Rules
        rule = LifecycleService.TRANSITION_RULES.get((current_status, new_status))
        
        if not rule:
            # Check for generic "Archived" or "On Hold"
            if new_status in [ProjectStatus.ARCHIVED, ProjectStatus.ON_HOLD]:
                if changed_by_user.role not in [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD]:
                     raise HTTPException(status_code=403, detail="Insufficient permissions to archive/hold project")
            elif changed_by_user.role != UserRole.ADMIN:
                 raise HTTPException(status_code=400, detail=f"Invalid status transition from {current_status} to {new_status}")
        else:
            if changed_by_user.role not in rule["allowed_roles"] and changed_by_user.role != UserRole.ADMIN:
                 raise HTTPException(status_code=403, detail="Insufficient permissions for this status change")
            
            if "min_score" in rule:
                min_score = rule["min_score"]
                current_score = project.afcen_score or 0
                if current_score < min_score:
                     raise HTTPException(status_code=400, detail=f"Project score {current_score} is below minimum {min_score} required for {new_status}")

        # 3. Apply Change
        project.status = new_status
        
        # 4. Record History
        history = ProjectStatusHistory(
            project_id=project.id,
            previous_status=current_status,
            new_status=new_status,
            changed_by_id=changed_by_user.id,
            change_date=datetime.utcnow(),
            reason=reason,
            notes=notes,
            is_automated=is_automated
        )
        db.add(history)
        await db.commit()
        await db.refresh(project)
        
        return project

    @staticmethod
    def get_available_transitions(current_status: ProjectStatus, user_role: UserRole) -> List[ProjectStatus]:
        """
        Returns list of allowed status transitions for a user.
        """
        allowed = []
        for (from_s, to_s), rule in LifecycleService.TRANSITION_RULES.items():
            if from_s == current_status:
                if user_role in rule["allowed_roles"] or user_role == UserRole.ADMIN:
                    allowed.append(to_s)
        
        # Add generic transitions allowed for admins/leads
        if user_role in [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD]:
            if ProjectStatus.ARCHIVED not in allowed and current_status != ProjectStatus.ARCHIVED:
                allowed.append(ProjectStatus.ARCHIVED)
            if ProjectStatus.ON_HOLD not in allowed and current_status != ProjectStatus.ON_HOLD:
                allowed.append(ProjectStatus.ON_HOLD)
                
        return allowed
