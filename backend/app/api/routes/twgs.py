from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
import uuid

from app.core.database import get_db
from app.models.models import TWG, User, UserRole, Meeting, Project, ActionItem, Document, MeetingStatus, ActionItemStatus
from app.schemas.schemas import TWGCreate, TWGRead, TWGUpdate
from app.api.deps import get_current_active_user, require_admin, require_facilitator

router = APIRouter(prefix="/twgs", tags=["TWGs"])

@router.post("/", response_model=TWGRead, status_code=status.HTTP_201_CREATED)
async def create_twg(
    twg_in: TWGCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new TWG.
    
    Requires ADMIN role.
    """
    db_twg = TWG(**twg_in.model_dump())
    db.add(db_twg)
    await db.commit()
    await db.refresh(db_twg)
    return db_twg

@router.get("/", response_model=List[TWGRead])
async def list_twgs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all TWGs.
    
    Accessible to all active users.
    """
    # Common loading options with selectinload for leads
    query_options = [
        selectinload(TWG.political_lead),
        selectinload(TWG.technical_lead),
    ]
    
    # We will need to perform separate queries or use scalar subqueries for stats.
    # For simplicity and clarity in this iteration, let's fetch IDs and then load stats.
    # A more optimized approach would use group_by and multiple queries.
    
    result = await db.execute(select(TWG).options(*query_options).offset(skip).limit(limit))
    twgs = result.scalars().all()
    
    # Enrich with stats
    for twg in twgs:
        # Meetings Held (Completed)
        meetings_res = await db.execute(
            select(func.count(Meeting.id)).where(Meeting.twg_id == twg.id, Meeting.status == MeetingStatus.COMPLETED)
        )
        meetings_held = meetings_res.scalar() or 0
        
        # Open Actions (Not Completed)
        actions_res = await db.execute(
            select(func.count(ActionItem.id)).where(TWG.id == twg.id, ActionItem.twg_id == twg.id, ActionItem.status.in_([ActionItemStatus.PENDING, ActionItemStatus.IN_PROGRESS, ActionItemStatus.OVERDUE]))
        )
        open_actions = actions_res.scalar() or 0
        
        # Pipeline Projects (All)
        projects_res = await db.execute(
             select(func.count(Project.id)).where(Project.twg_id == twg.id)
        )
        pipeline_projects = projects_res.scalar() or 0
        
        # Resources (Documents)
        docs_res = await db.execute(
            select(func.count(Document.id)).where(Document.twg_id == twg.id)
        )
        resources_count = docs_res.scalar() or 0
        
        twg.stats = {
            "meetings_held": meetings_held,
            "open_actions": open_actions,
            "pipeline_projects": pipeline_projects,
            "resources_count": resources_count
        }
        
    return twgs

@router.get("/{twg_id}", response_model=TWGRead)
async def get_twg(
    twg_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get TWG details by ID with stats.
    """
    result = await db.execute(
        select(TWG)
        .options(
            selectinload(TWG.political_lead),
            selectinload(TWG.technical_lead),
            selectinload(TWG.action_items).selectinload(ActionItem.owner),
            selectinload(TWG.documents).selectinload(Document.uploaded_by)
        )
        .where(TWG.id == twg_id)
    )
    db_twg = result.scalar_one_or_none()
    if not db_twg:
        raise HTTPException(status_code=404, detail="TWG not found")
        
    # Fetch stats
    # Meetings Held
    meetings_res = await db.execute(
        select(func.count(Meeting.id)).where(Meeting.twg_id == twg_id, Meeting.status == MeetingStatus.COMPLETED)
    )
    meetings_held = meetings_res.scalar() or 0
    
    # Open Actions
    actions_res = await db.execute(
        select(func.count(ActionItem.id)).where(ActionItem.twg_id == twg_id, ActionItem.status.in_([ActionItemStatus.PENDING, ActionItemStatus.IN_PROGRESS, ActionItemStatus.OVERDUE]))
    )
    open_actions = actions_res.scalar() or 0
    
    # Pipeline Projects
    projects_res = await db.execute(
            select(func.count(Project.id)).where(Project.twg_id == twg_id)
    )
    pipeline_projects = projects_res.scalar() or 0
    
    # Resources
    docs_res = await db.execute(
        select(func.count(Document.id)).where(Document.twg_id == twg_id)
    )
    resources_count = docs_res.scalar() or 0
    
    db_twg.stats = {
        "meetings_held": meetings_held,
        "open_actions": open_actions,
        "pipeline_projects": pipeline_projects,
        "resources_count": resources_count
    }

    return db_twg

@router.patch("/{twg_id}", response_model=TWGRead)
async def update_twg(
    twg_id: uuid.UUID,
    twg_in: TWGUpdate,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Update TWG details.
    
    Requires ADMIN or FACILITATOR role.
    If FACILITATOR, ideally should check if assigned to this TWG (logic can be added).
    """
    result = await db.execute(
        select(TWG)
        .options(
            selectinload(TWG.political_lead),
            selectinload(TWG.technical_lead),
            selectinload(TWG.action_items),
            selectinload(TWG.documents),
        )
        .where(TWG.id == twg_id)
    )
    db_twg = result.scalar_one_or_none()
    if not db_twg:
        raise HTTPException(status_code=404, detail="TWG not found")
    
    # Additional check: If facilitator, ensure they are the lead?
    # For now, allow generic facilitator access as per simplified reqs.
    # Admins can edit anything.
    
    update_data = twg_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_twg, key, value)
    
    await db.commit()
    # Refresh with eager loading to ensure relationships are loaded
    await db.refresh(db_twg, attribute_names=['political_lead', 'technical_lead', 'action_items', 'documents'])
    return db_twg
