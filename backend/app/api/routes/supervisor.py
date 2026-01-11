"""
Supervisor API Routes

Endpoints for accessing supervisor global state.
Admin-only access with real-time WebSocket updates.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.models import User, UserRole
from app.services.supervisor_state_service import get_supervisor_state
from app.schemas.supervisor import (
    SupervisorStateSnapshot,
    GlobalCalendarResponse,
    DocumentRegistryResponse,
    ProjectPipelineResponse,
    TWGSummary
)
from app.core.ws_manager import ws_manager

router = APIRouter(prefix="/supervisor", tags=["supervisor"])


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin access required for supervisor state"
        )
    return current_user


@router.get("/state", response_model=SupervisorStateSnapshot)
async def get_global_state(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get complete supervisor global state.
    
    **Admin Only**
    
    Returns unified view of:
    - All TWG meetings (global calendar)
    - All documents (document registry)
    - All projects (pipeline view)
    - TWG summaries
    - Active conflicts
    """
    state_service = get_supervisor_state()
    
    # Refresh state from database (real-time)
    state = await state_service.refresh_state(db)
    
    return state


@router.get("/state/calendar", response_model=GlobalCalendarResponse)
async def get_global_calendar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get unified calendar of all TWG meetings.
    
    **Admin Only**
    
    Returns all meetings across all TWGs with conflict indicators.
    """
    state_service = get_supervisor_state()
    
    # Ensure state is fresh
    await state_service.refresh_state(db)
    
    return state_service.get_global_calendar()


@router.get("/state/documents", response_model=DocumentRegistryResponse)
async def get_document_registry(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get document registry with all documents.
    
    **Admin Only**
    
    Returns all documents with metadata and TWG breakdown.
    """
    state_service = get_supervisor_state()
    
    # Ensure state is fresh
    await state_service.refresh_state(db)
    
    return state_service.get_document_registry()


@router.get("/state/projects", response_model=ProjectPipelineResponse)
async def get_project_pipeline(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get project pipeline view.
    
    **Admin Only**
    
    Returns all projects grouped by status and TWG.
    """
    state_service = get_supervisor_state()
    
    # Ensure state is fresh
    await state_service.refresh_state(db)
    
    return state_service.get_project_pipeline()


@router.get("/state/twg/{twg_id}", response_model=TWGSummary)
async def get_twg_summary(
    twg_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get summary for specific TWG.
    
    **Access Control**:
    - Admins: Can access any TWG
    - TWG Facilitators/Members: Can only access their own TWG
    """
    state_service = get_supervisor_state()
    
    # Ensure state is fresh
    await state_service.refresh_state(db)
    
    # RBAC: Check if user has access to this TWG
    is_admin = current_user.role == UserRole.ADMIN
    user_twg_ids = [twg.id for twg in current_user.twgs]
    
    if not is_admin and twg_id not in user_twg_ids:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this TWG's summary"
        )
    
    summary = state_service.get_twg_summary(twg_id)
    
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"TWG {twg_id} not found"
        )
    
    return summary


@router.post("/state/refresh")
async def force_state_refresh(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Force immediate state refresh.
    
    **Admin Only**
    
    Triggers real-time state update and broadcasts to connected clients.
    """
    state_service = get_supervisor_state()
    
    # Refresh state
    state = await state_service.refresh_state(db)
    
    # Broadcast update to all connected WebSocket clients
    await ws_manager.broadcast({
        "type": "supervisor_state_updated",
        "timestamp": state.last_refresh.isoformat(),
        "summary": {
            "total_meetings": state.total_meetings,
            "total_documents": state.total_documents,
            "total_projects": state.total_projects,
            "active_conflicts": len(state.active_conflicts)
        }
    })
    
    return {
        "status": "refreshed",
        "last_refresh": state.last_refresh,
        "summary": {
            "total_twgs": state.total_twgs,
            "total_meetings": state.total_meetings,
            "total_documents": state.total_documents,
            "total_projects": state.total_projects,
            "active_conflicts": len(state.active_conflicts)
        }
    }
