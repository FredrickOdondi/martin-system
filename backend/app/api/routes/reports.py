from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
from loguru import logger

from backend.app.core.database import get_db
from app.models.models import Report, ReportType, ReportStatus, User
from backend.app.schemas.schemas import ReportCreate, ReportRead, ReportUpdate
from backend.app.api.deps import get_current_active_user, require_facilitator
from backend.app.agents.supervisor import SupervisorAgent

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/generate", response_model=ReportRead)
async def generate_report(
    report_type: ReportType,
    title: str,
    twg_id: Optional[uuid.UUID] = None,
    instructions: Optional[str] = None,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new report using the Supervisor Agent.
    The report is saved as DRAFT.
    """
    supervisor = SupervisorAgent(keep_history=False)
    
    content = ""
    
    # Logic to map ReportType to Supervisor methods
    try:
        if report_type == ReportType.DECLARATION:
             # Basic implementation: declaration usually requires input from all TWGs
             # We might need a better way to pass specific sections if they are already drafted
             # For now, we simulate by collecting status or using generic synthesis
             # Ideally, we should have a 'synthesize_declaration' wrapper in Supervisor that does the heavy lifting
             # But Supervisor.document_synthesizer.synthesize_declaration needs structured inputs.
             # Let's use supervisor to create a draft based on current context.
             
             # If instructions are provided, we can ask supervisor to draft it
             if instructions:
                 content = supervisor.chat(f"Draft a declaration with title '{title}' based on these instructions: {instructions}")
             else:
                 # Auto-generate based on system state
                 # This is complex, potentially slow. We'll use a placeholder or simple synthesis for now.
                 priorities = supervisor.generate_strategic_priorities()
                 content = supervisor.chat(f"Draft a formal Declaration entitled '{title}' incorporating these strategic priorities:\n\n{priorities}")

        elif report_type == ReportType.SUMMIT_REPORT:
            content = supervisor.generate_summit_readiness_assessment() # Close enough for now
            
        elif report_type == ReportType.POLICY_BRIEF:
             content = supervisor.generate_policy_coherence_check() # Reuse this for now
             
        elif report_type == ReportType.CONCEPT_NOTE:
             if not instructions:
                 raise HTTPException(status_code=400, detail="Instructions required for Concept Note")
             content = supervisor.chat(f"Draft a Concept Note for '{title}'. Details: {instructions}")
             
        elif report_type == ReportType.TECHNICAL_REPORT:
             # If TWG ID provided, maybe focus on that
             if twg_id:
                 # We need to find the agent name from ID. 
                 # This is tricky without querying DB to get TWG name -> Agent ID mapping.
                 # For now, we'll just use the supervisor generic chat.
                 pass
             content = supervisor.chat(f"Draft a Technical Report on '{title}'. {instructions or ''}")
             
        else:
             content = supervisor.chat(f"Draft a document of type '{report_type}' with title '{title}'. {instructions or ''}")

    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    # Create Report Record
    db_report = Report(
        title=title,
        type=report_type,
        content=content,
        status=ReportStatus.DRAFT,
        version="0.1",
        twg_id=twg_id,
        created_by_id=current_user.id
    )
    
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    
    return db_report

@router.get("/", response_model=List[ReportRead])
async def list_reports(
    twg_id: Optional[uuid.UUID] = None,
    status: Optional[ReportStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List reports.
    """
    query = select(Report)
    
    if twg_id:
        query = query.where(Report.twg_id == twg_id)
        
    if status:
        query = query.where(Report.status == status)
        
    # Check permissions? Assuming members can view reports.
    # If strictly per TWG, we should filter users who don't have access.
    # For now, assume global visibility or implemented filters.
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{report_id}", response_model=ReportRead)
async def get_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific report.
    """
    query = select(Report).where(Report.id == report_id)
    result = await db.execute(query)
    db_report = result.scalar_one_or_none()
    
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    return db_report

@router.patch("/{report_id}", response_model=ReportRead)
async def update_report(
    report_id: uuid.UUID,
    report_in: ReportUpdate,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a report (Content, Status, Version).
    This is used for APPROVAL (setting status to APPROVED/FINAL).
    """
    query = select(Report).where(Report.id == report_id)
    result = await db.execute(query)
    db_report = result.scalar_one_or_none()
    
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Logic to ensure proper versioning?
    # e.g., if status goes from Draft -> Final, version increments?
    # For now, trust the input.
    
    update_data = report_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_report, key, value)
        
    # Update updated_at? handled by onupdate
    
    await db.commit()
    await db.refresh(db_report)
    
    return db_report
