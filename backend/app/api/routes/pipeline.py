"""
Deal Pipeline API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path as PathParam
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, UTC
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Project, ProjectStatus
from app.services.project_pipeline_service import ProjectPipelineService
from app.services.investor_matching_service import get_investor_matching_service
from app.schemas.pipeline_schemas import (
    ProjectIngest, ProjectPipelineRead, ProjectAdvanceStage, 
    InvestorMatchRead, PipelineStats, InvestorMatchUpdate, InvestorRead
)

router = APIRouter(prefix="/pipeline", tags=["deal-pipeline"])


@router.get("/", response_model=List[ProjectPipelineRead])
async def list_pipeline_projects(
    stage: Optional[ProjectStatus] = None,
    pillar: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List projects in the deal pipeline with optional filtering.
    """
    query = select(Project)
    
    if stage:
        query = query.where(Project.status == stage)
    if pillar:
        # Case-insensitive pillar filter
        query = query.where(Project.pillar.ilike(f"%{pillar}%"))
        
    result = await db.execute(query)
    projects = result.scalars().all()
    
    # Map to schema
    return [
        ProjectPipelineRead(
            id=p.id,
            name=p.name,
            description=p.description,
            status=p.status,
            investment_size=p.investment_size,
            currency=p.currency,
            readiness_score=p.readiness_score,
            afcen_score=p.afcen_score,
            strategic_alignment_score=p.strategic_alignment_score,
            lead_country=p.lead_country,
            pillar=p.pillar,
            assigned_agent=p.assigned_agent,
            updated_at=getattr(p, 'created_at', datetime.now(UTC))
        ) for p in projects
    ]

@router.post("/ingest", response_model=ProjectPipelineRead)
async def ingest_project(
    data: ProjectIngest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingest a new project proposal and calculate initial scores.
    """
    service = ProjectPipelineService(db)
    
    result = await service.ingest_project_proposal(
        data=data.model_dump(),
        submitted_by_user_id=current_user.id
    )
    
    p = result["project"]
    return ProjectPipelineRead(
        id=p.id,
        name=p.name,
        description=p.description,
        status=p.status,
        investment_size=p.investment_size,
        currency=p.currency,
        readiness_score=p.readiness_score,
        afcen_score=p.afcen_score,
        strategic_alignment_score=p.strategic_alignment_score,
        lead_country=p.lead_country,
        pillar=p.pillar,
        assigned_agent=p.assigned_agent,
        updated_at=getattr(p, 'created_at', datetime.now(UTC))
    )

@router.get("/{project_id}", response_model=ProjectPipelineRead)
async def get_project_details(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed project view.
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalars().first()
    
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return ProjectPipelineRead(
        id=p.id,
        name=p.name,
        description=p.description,
        status=p.status,
        investment_size=p.investment_size,
        currency=p.currency,
        readiness_score=p.readiness_score,
        afcen_score=p.afcen_score,
        strategic_alignment_score=p.strategic_alignment_score,
        lead_country=p.lead_country,
        pillar=p.pillar,
        assigned_agent=p.assigned_agent,
        updated_at=getattr(p, 'created_at', datetime.now(UTC))
    )

@router.post("/{project_id}/advance", response_model=ProjectPipelineRead)
async def advance_project_stage(
    project_id: uuid.UUID,
    payload: ProjectAdvanceStage,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Advance a project to the next stage.
    """
    service = ProjectPipelineService(db)
    
    result = await service.advance_project_stage(
        project_id=project_id,
        new_stage=payload.new_stage,
        advanced_by_user_id=current_user.id,
        notes=payload.notes
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    p = result["project"]
    return ProjectPipelineRead(
        id=p.id,
        name=p.name,
        description=p.description,
        status=p.status,
        investment_size=p.investment_size,
        currency=p.currency,
        readiness_score=p.readiness_score,
        afcen_score=p.afcen_score,
        strategic_alignment_score=p.strategic_alignment_score,
        lead_country=p.lead_country,
        pillar=p.pillar,
        assigned_agent=p.assigned_agent,
        updated_at=getattr(p, 'created_at', datetime.now(UTC))
    )

@router.get("/{project_id}/matches", response_model=List[InvestorMatchRead])
async def get_project_matches(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get investor matches for a project.
    """
    service = get_investor_matching_service(db)
    matches = await service.get_matches_for_project(project_id)
    
    return [
        InvestorMatchRead(
            match_id=m["match_id"],
            investor=InvestorRead(
                id=m["investor"].id,
                name=m["investor"].name,
                sector_preferences=m["investor"].sector_preferences,
                ticket_size_min=m["investor"].ticket_size_min,
                ticket_size_max=m["investor"].ticket_size_max,
                geographic_focus=m["investor"].geographic_focus,
                investment_instruments=m["investor"].investment_instruments
            ),
            score=m["score"],
            status=m["status"],
            notes=m["notes"]
        ) for m in matches
    ]

@router.patch("/matches/{match_id}", response_model=dict)
async def update_match_status(
    match_id: uuid.UUID,
    payload: InvestorMatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update match status (e.g. to INTERESTED to trigger Protocol Agent).
    """
    service = get_investor_matching_service(db)
    result = await service.update_match_status(
        match_id=match_id,
        new_status=payload.status,
        notes=payload.notes,
        updated_by_user_id=current_user.id
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
        
    return result

@router.post("/{project_id}/match", response_model=dict)
async def trigger_investor_matching(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger investor matching for a project.
    """
    service = get_investor_matching_service(db)
    result = await service.match_investors(project_id)
    return result

@router.get("/dashboard/stats", response_model=PipelineStats)
async def get_pipeline_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get high-level pipeline statistics.
    """
    service = ProjectPipelineService(db)
    stats = await service.check_pipeline_health()
    return PipelineStats(**stats)
