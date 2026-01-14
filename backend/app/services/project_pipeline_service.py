"""
Project Pipeline Coordinator Service

Manages the investment project lifecycle through defined stages:
Identification -> Vetting -> Due Diligence -> Financing -> Deal Room -> Bankable -> Presented

Coordinates with TWG agents for vetting and provides pipeline health monitoring.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, UTC, timedelta
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from decimal import Decimal

from app.models.models import (
    Project, ProjectStatus, TWG, TWGPillar,
    ActionItem, ActionItemStatus, ActionItemPriority
)
from app.services.audit_service import audit_service


VALID_TRANSITIONS: Dict[ProjectStatus, List[ProjectStatus]] = {
    ProjectStatus.IDENTIFIED: [ProjectStatus.VETTING],
    ProjectStatus.VETTING: [ProjectStatus.DUE_DILIGENCE, ProjectStatus.IDENTIFIED],
    ProjectStatus.DUE_DILIGENCE: [ProjectStatus.FINANCING, ProjectStatus.VETTING],
    ProjectStatus.FINANCING: [ProjectStatus.DEAL_ROOM, ProjectStatus.DUE_DILIGENCE],
    ProjectStatus.DEAL_ROOM: [ProjectStatus.BANKABLE, ProjectStatus.FINANCING],
    ProjectStatus.BANKABLE: [ProjectStatus.PRESENTED, ProjectStatus.DEAL_ROOM],
    ProjectStatus.PRESENTED: [],
}

STALL_THRESHOLDS_DAYS: Dict[ProjectStatus, int] = {
    ProjectStatus.IDENTIFIED: 14,
    ProjectStatus.VETTING: 21,
    ProjectStatus.DUE_DILIGENCE: 30,
    ProjectStatus.FINANCING: 45,
    ProjectStatus.DEAL_ROOM: 30,
    ProjectStatus.BANKABLE: 14,
}


class ProjectPipelineService:
    """
    Service for coordinating project lifecycle and pipeline health.
    
    Manages:
    - Stage transitions with validation
    - Automatic task delegation to Resource Mobilization agent
    - Pipeline health monitoring for stalled projects
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize project pipeline service.

        Args:
            db: Async database session
        """
        self.db = db

    async def advance_project_stage(
        self,
        project_id: uuid.UUID,
        new_stage: ProjectStatus,
        advanced_by_user_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Advance a project to a new stage with validation.

        Args:
            project_id: ID of the project to advance
            new_stage: The target stage
            advanced_by_user_id: User performing the transition
            notes: Optional notes about the transition

        Returns:
            Dict with project and status, or error if invalid transition
        """
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalars().first()

        if not project:
            return {"error": "Project not found", "project": None}

        current_stage = project.status
        allowed_transitions = VALID_TRANSITIONS.get(current_stage, [])

        if new_stage not in allowed_transitions:
            logger.warning(
                f"Invalid transition attempted: {current_stage.value} -> {new_stage.value} "
                f"for project {project_id}"
            )
            return {
                "error": f"Invalid transition from {current_stage.value} to {new_stage.value}. "
                         f"Allowed: {[s.value for s in allowed_transitions]}",
                "project": project,
                "current_stage": current_stage.value
            }

        old_stage = project.status
        project.status = new_stage

        project.metadata_json = {
            **(project.metadata_json or {}),
            "last_stage_change": datetime.now(UTC).isoformat(),
            "stage_history": (project.metadata_json or {}).get("stage_history", []) + [{
                "from": old_stage.value,
                "to": new_stage.value,
                "at": datetime.now(UTC).isoformat(),
                "by": str(advanced_by_user_id) if advanced_by_user_id else None,
                "notes": notes
            }]
        }

        if advanced_by_user_id:
            await audit_service.log_activity(
                db=self.db,
                user_id=advanced_by_user_id,
                action="project_stage_change",
                resource_type="project",
                resource_id=project.id,
                details={
                    "from_stage": old_stage.value,
                    "to_stage": new_stage.value,
                    "notes": notes
                }
            )

        if new_stage == ProjectStatus.DUE_DILIGENCE:
            vetting_result = await self.request_investment_vetting(
                project_id=project.id,
                requested_by_user_id=advanced_by_user_id
            )
            logger.info(f"Auto-created vetting task for project {project_id}: {vetting_result}")

        if new_stage == ProjectStatus.FINANCING:
            # Trigger Investor Matching
            from app.services.investor_matching_service import get_investor_matching_service
            matching_service = get_investor_matching_service(self.db)
            match_result = await matching_service.match_investors(project_id)
            logger.info(f"Auto-triggered investor matching for project {project_id}: {match_result}")

        await self.db.commit()
        await self.db.refresh(project)

        logger.info(
            f"✓ Project {project.name} transitioned: {old_stage.value} -> {new_stage.value}"
        )

        return {
            "project": project,
            "status": "success",
            "from_stage": old_stage.value,
            "to_stage": new_stage.value
        }

    async def request_investment_vetting(
        self,
        project_id: uuid.UUID,
        requested_by_user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Delegate a vetting task to the Resource Mobilization agent.

        Creates an ActionItem assigned to the Resource Mobilization TWG
        for conducting due diligence on the project.

        Args:
            project_id: ID of the project to vet
            requested_by_user_id: User requesting the vetting

        Returns:
            Dict with the created action item or error
        """
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalars().first()

        if not project:
            return {"error": "Project not found", "action_item": None}

        rm_twg_result = await self.db.execute(
            select(TWG).where(TWG.pillar == TWGPillar.resource_mobilization)
        )
        rm_twg = rm_twg_result.scalars().first()

        if not rm_twg:
            logger.warning("Resource Mobilization TWG not found")
            return {"error": "Resource Mobilization TWG not found", "action_item": None}

        owner_id = rm_twg.technical_lead_id or rm_twg.political_lead_id
        if not owner_id:
            return {"error": "Resource Mobilization TWG has no lead assigned", "action_item": None}

        action_item = ActionItem(
            twg_id=rm_twg.id,
            description=(
                f"Investment Vetting Required: {project.name}\n\n"
                f"Project Description: {project.description}\n"
                f"Investment Size: {project.currency} {project.investment_size:,.2f}\n"
                f"Current Readiness Score: {project.readiness_score}\n\n"
                f"Please conduct due diligence and update the project readiness assessment."
            ),
            owner_id=owner_id,
            due_date=datetime.now(UTC) + timedelta(days=14),
            status=ActionItemStatus.PENDING,
            priority=ActionItemPriority.HIGH
        )

        self.db.add(action_item)
        await self.db.flush()

        if requested_by_user_id:
            await audit_service.log_activity(
                db=self.db,
                user_id=requested_by_user_id,
                action="investment_vetting_requested",
                resource_type="action_item",
                resource_id=action_item.id,
                details={
                    "project_id": str(project_id),
                    "project_name": project.name,
                    "assigned_to_twg": rm_twg.name
                }
            )

        logger.info(
            f"✓ Vetting task created for project {project.name} -> "
            f"Resource Mobilization TWG (ActionItem: {action_item.id})"
        )

        return {
            "action_item": action_item,
            "status": "created",
            "assigned_to_twg": rm_twg.name
        }

    async def check_pipeline_health(self) -> Dict[str, Any]:
        """
        Identify stalled projects in the pipeline.

        Checks each project against stage-specific thresholds to detect
        projects that may need attention.

        Returns:
            Dict with:
                - stalled_projects: List of projects exceeding their stage threshold
                - healthy_projects: Count of projects within thresholds
                - by_stage: Breakdown by stage
        """
        result = await self.db.execute(select(Project))
        projects = result.scalars().all()

        stalled_projects = []
        healthy_count = 0
        by_stage: Dict[str, Dict[str, int]] = {}

        now = datetime.now(UTC)

        for project in projects:
            stage = project.status
            stage_key = stage.value

            if stage_key not in by_stage:
                by_stage[stage_key] = {"total": 0, "stalled": 0}
            by_stage[stage_key]["total"] += 1

            if stage == ProjectStatus.PRESENTED:
                healthy_count += 1
                continue

            last_change_str = (project.metadata_json or {}).get("last_stage_change")
            if last_change_str:
                try:
                    last_change = datetime.fromisoformat(last_change_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    last_change = now
            else:
                last_change = now

            threshold_days = STALL_THRESHOLDS_DAYS.get(stage, 30)
            days_in_stage = (now - last_change).days

            if days_in_stage > threshold_days:
                stalled_projects.append({
                    "project_id": str(project.id),
                    "name": project.name,
                    "stage": stage.value,
                    "days_in_stage": days_in_stage,
                    "threshold_days": threshold_days,
                    "overdue_by": days_in_stage - threshold_days
                })
                by_stage[stage_key]["stalled"] += 1
            else:
                healthy_count += 1

        logger.info(
            f"Pipeline health check: {healthy_count} healthy, "
            f"{len(stalled_projects)} stalled projects"
        )

        return {
            "stalled_projects": stalled_projects,
            "healthy_projects": healthy_count,
            "total_projects": len(projects),
            "by_stage": by_stage,
            "checked_at": datetime.now(UTC).isoformat()
        }

    async def get_project_stage_info(self, project_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get information about a project's current stage and available transitions.

        Args:
            project_id: ID of the project

        Returns:
            Dict with current stage, history, and allowed transitions
        """
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalars().first()

        if not project:
            return {"error": "Project not found"}

        current_stage = project.status
        allowed_transitions = VALID_TRANSITIONS.get(current_stage, [])

        return {
            "project_id": str(project.id),
            "name": project.name,
            "current_stage": current_stage.value,
            "allowed_transitions": [s.value for s in allowed_transitions],
            "stage_history": (project.metadata_json or {}).get("stage_history", []),
            "last_stage_change": (project.metadata_json or {}).get("last_stage_change")
        }

    def calculate_afcen_score(
        self,
        readiness_score: float,
        strategic_alignment_score: float,
        regional_impact_score: Optional[float] = None
    ) -> Decimal:
        """
        Calculate the composite AfCEN score (0-999.99).
        
        Algorithm:
        - Readiness Score (0-10): 40% weight
        - Strategic Alignment (0-10): 30% weight
        - Regional Impact (0-10): 30% weight
        
        Result is scaled to 0-100 range.
        
        Args:
            readiness_score: Project readiness (0-10)
            strategic_alignment_score: Strategic fit (0-10)
            regional_impact_score: Optional impact score, defaults to 5.0 if not provided
            
        Returns:
            Decimal score
        """
        # Ensure inputs are within bounds (0-10)
        r_score = max(0.0, min(10.0, float(readiness_score)))
        s_score = max(0.0, min(10.0, float(strategic_alignment_score)))
        if regional_impact_score is not None:
             i_score = max(0.0, min(10.0, float(regional_impact_score)))
        else:
             i_score = 5.0
        
        # Calculate weighted sum
        weighted_sum = (r_score * 0.4) + (s_score * 0.3) + (i_score * 0.3)
        
        # Scale to 0-100
        final_score = weighted_sum * 10
        
        return Decimal(f"{final_score:.2f}")

    async def ingest_project_proposal(
        self,
        data: Dict[str, Any],
        submitted_by_user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Ingest a new project proposal and auto-calculate initial scores.
        
        Args:
            data: Project data dictionary
            submitted_by_user_id: User submitting the proposal
            
        Returns:
            Created Project object and status
        """
        # Calculate initial AfCEN score
        readiness = data.get("readiness_score", 0.0)
        strategic_align = data.get("strategic_alignment_score", 0.0)
        
        afcen_score = self.calculate_afcen_score(
            readiness_score=readiness,
            strategic_alignment_score=strategic_align
        )
        
        # Create Project
        project = Project(
            twg_id=uuid.UUID(data["twg_id"]),
            name=data["name"],
            description=data["description"],
            investment_size=data["investment_size"],
            currency=data.get("currency", "USD"),
            readiness_score=readiness,
            status=ProjectStatus.IDENTIFIED,
            pillar=data.get("pillar"),
            lead_country=data.get("lead_country"),
            afcen_score=afcen_score,
            strategic_alignment_score=Decimal(str(strategic_align)),
            assigned_agent=data.get("assigned_agent"),
            metadata_json={
                "source": "ingestion_api",
                "submitted_at": datetime.now(UTC).isoformat(),
                "submitted_by": str(submitted_by_user_id) if submitted_by_user_id else None
            }
        )
        
        self.db.add(project)
        await self.db.flush()
        
        if submitted_by_user_id:
            await audit_service.log_activity(
                db=self.db,
                user_id=submitted_by_user_id,
                action="project_ingested",
                resource_type="project",
                resource_id=project.id,
                details={
                    "name": project.name,
                    "afcen_score": str(afcen_score)
                }
            )
            
        await self.db.commit()
        await self.db.refresh(project)
        
        logger.info(f"✓ Project ingested: {project.name} (AfCEN Score: {afcen_score})")
        
        return {
            "project": project,
            "status": "created",
            "afcen_score": afcen_score
        }
