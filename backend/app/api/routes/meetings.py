from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from backend.app.core.database import get_db
from backend.app.models.models import Meeting, Agenda, Minutes, User, UserRole
from backend.app.schemas.schemas import MeetingCreate, MeetingRead
from backend.app.api.deps import get_current_active_user, require_facilitator, require_twg_access, has_twg_access

router = APIRouter(prefix="/meetings", tags=["Meetings"])

@router.post("/", response_model=MeetingRead, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting_in: MeetingCreate,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule a new meeting.
    
    Requires FACILITATOR or ADMIN role.
    User must have access to the TWG.
    """
    # Check if facilitator has access to this TWG
    if not has_twg_access(current_user, meeting_in.twg_id):
        raise HTTPException(status_code=403, detail="You do not have access to manage meetings for this TWG")

    db_meeting = Meeting(**meeting_in.model_dump())
    db.add(db_meeting)
    await db.commit()
    await db.refresh(db_meeting)
    return db_meeting

@router.get("/", response_model=List[MeetingRead])
async def list_meetings(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all meetings visible to the user.
    """
    # If admin, show all. If member, show only their TWG meetings.
    query = select(Meeting).offset(skip).limit(limit)
    
    if current_user.role != UserRole.ADMIN:
        # Get IDs of TWGs user belongs to
        user_twg_ids = [twg.id for twg in current_user.twgs]
        query = query.where(Meeting.twg_id.in_(user_twg_ids))
        
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{meeting_id}", response_model=MeetingRead)
async def get_meeting(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get meeting details.
    """
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Check access
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
        
    return db_meeting

@router.get("/{meeting_id}/agenda")
async def get_meeting_agenda(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify meeting exists and access rights
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(Agenda).where(Agenda.meeting_id == meeting_id))
    db_agenda = result.scalar_one_or_none()
    if not db_agenda:
        raise HTTPException(status_code=404, detail="Agenda not found")
    return db_agenda

@router.get("/{meeting_id}/minutes")
async def get_meeting_minutes(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify meeting exists and access rights
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(Minutes).where(Minutes.meeting_id == meeting_id))
    db_minutes = result.scalar_one_or_none()
    if not db_minutes:
        raise HTTPException(status_code=404, detail="Minutes not found")
    return db_minutes
