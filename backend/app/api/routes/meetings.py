from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.core.database import get_db
from app.models.models import Meeting, Agenda, Minutes, User, UserRole, MinutesStatus, MeetingParticipant, RsvpStatus, ActionItem, TWG, Document
from app.schemas.schemas import (
    MeetingCreate, MeetingRead, MeetingUpdate,
    MinutesCreate, MinutesUpdate, MinutesRead,
    AgendaCreate, AgendaRead, AgendaUpdate
)
from app.api.deps import get_current_active_user, require_facilitator, require_twg_access, has_twg_access
from app.services.email_service import email_service
from sqlalchemy.orm import selectinload

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
        
    query = query.options(
        selectinload(Meeting.participants),
        selectinload(Meeting.twg)
    )
        
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
    query = select(Meeting).where(Meeting.id == meeting_id).options(
        selectinload(Meeting.participants),
        selectinload(Meeting.agenda),
        selectinload(Meeting.minutes),
        selectinload(Meeting.twg)
    )
    result = await db.execute(query)
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

@router.patch("/{meeting_id}", response_model=MeetingRead)
async def update_meeting(
    meeting_id: uuid.UUID,
    meeting_in: MeetingUpdate,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Update meeting details (e.g., add transcript, change status).
    """
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
        
    update_data = meeting_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_meeting, key, value)
        
    await db.commit()
    await db.refresh(db_meeting)
    return db_meeting

@router.post("/{meeting_id}/minutes", response_model=MinutesRead)
async def upsert_minutes(
    meeting_id: uuid.UUID,
    minutes_in: MinutesUpdate, # Allow partial updates or full content
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Create or Update meeting minutes.
    """
    # Verify meeting
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Check for existing minutes
    result = await db.execute(select(Minutes).where(Minutes.meeting_id == meeting_id))
    db_minutes = result.scalar_one_or_none()
    
    if db_minutes:
        # Update
        update_data = minutes_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_minutes, key, value)
    else:
        # Create
        if not minutes_in.content:
             raise HTTPException(status_code=400, detail="Content required for creating minutes")
             
        minutes_data = minutes_in.model_dump(exclude_unset=True)
        # partial update schema used for creation, ensure defaults or required
        db_minutes = Minutes(meeting_id=meeting_id, **minutes_data)
        db.add(db_minutes)
        
    await db.commit()
    await db.refresh(db_minutes)
    return db_minutes

@router.post("/{meeting_id}/schedule", status_code=status.HTTP_200_OK)
async def schedule_meeting_trigger(
    meeting_id: uuid.UUID,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Finalize and schedule a meeting. 
    Triggers automated email invitations and calendar invites.
    """
    # Verify meeting exists and access rights
    query = select(Meeting).where(Meeting.id == meeting_id).options(
        selectinload(Meeting.participants),
        selectinload(Meeting.twg)
    )

    result = await db.execute(query)
    db_meeting = result.scalar_one_or_none()

    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")

    if not db_meeting.participants:
        raise HTTPException(status_code=400, detail="No participants assigned to this meeting")

    # Change status
    db_meeting.status = MeetingStatus.SCHEDULED

    # Send emails
    participant_emails = []
    # db_meeting.participants is now List[User] objects
    for user in db_meeting.participants:
        if user.email:
            participant_emails.append(user.email)
            
    # Remove duplicates
    participant_emails = list(set(participant_emails))
    
    try:
        if participant_emails:
            await email_service.send_meeting_invite(
            to_emails=participant_emails,
            subject=f"INVITATION: {db_meeting.title}",
            template_name="meeting_invite.html",
            template_context={
                "user_name": "Valued Participant", # Simplified
                "meeting_title": db_meeting.title,
                "meeting_date": db_meeting.scheduled_at.strftime("%Y-%m-%d"),
                "meeting_time": db_meeting.scheduled_at.strftime("%H:%M UTC"),
                "location": db_meeting.location or "Virtual",
                "pillar_name": db_meeting.twg.pillar.value,
                "portal_url": "https://summit.ecowas.int/twg/portal" # Placeholder
            },
            meeting_details={
                "title": db_meeting.title,
                "start_time": db_meeting.scheduled_at,
                "duration": db_meeting.duration_minutes,
                "location": db_meeting.location
            }
        )
    except Exception as e:
        # Log error but don't fail the whole request? 
        # Actually, for scheduling, we want to know if it failed.
        raise HTTPException(status_code=500, detail=f"Failed to send invitations: {str(e)}")

    await db.commit()
    return {"status": "successfully scheduled", "emails_sent": len(participant_emails)}

# TODO: Refactor participant management to work with many-to-many User relationship
# The MeetingParticipant model no longer exists - participants are now User objects
# @router.post("/{meeting_id}/participants", response_model=List[MeetingParticipantRead])
# async def add_participants(
#     meeting_id: uuid.UUID,
#     participants: List[MeetingParticipantCreate],
#     current_user: User = Depends(require_facilitator),
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Add participants (users or external guests) to a meeting.
#     """
#     # Needs refactoring for new model structure
#     pass

@router.post("/{meeting_id}/agenda", response_model=AgendaRead)
async def upsert_agenda(
    meeting_id: uuid.UUID,
    agenda_in: AgendaCreate,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Create or Update meeting agenda.
    """
    # Verify meeting
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Check existing
    result = await db.execute(select(Agenda).where(Agenda.meeting_id == meeting_id))
    db_agenda = result.scalar_one_or_none()
    
    if db_agenda:
        db_agenda.content = agenda_in.content
    else:
        db_agenda = Agenda(meeting_id=meeting_id, content=agenda_in.content)
        db.add(db_agenda)
        
    await db.commit()
    await db.refresh(db_agenda)
    return db_agenda


@router.put("/{meeting_id}/participants/{participant_id}/rsvp", response_model=MeetingParticipantRead)
async def update_participant_rsvp(
    meeting_id: uuid.UUID,
    participant_id: uuid.UUID,
    rsvp_in: MeetingParticipantUpdate, # Just status
    current_user: User = Depends(require_facilitator), # Facilitator override aka "Fallback"
    db: AsyncSession = Depends(get_db)
):
    """
    Manually update a participant's RSVP status (RSVP Fallback).
    """
    # Verify meeting
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
        
    # Get participant
    result = await db.execute(select(MeetingParticipant).where(MeetingParticipant.id == participant_id))
    db_p = result.scalar_one_or_none()
    
    if not db_p:
        raise HTTPException(status_code=404, detail="Participant not found")
        
    if db_p.meeting_id != meeting_id:
        raise HTTPException(status_code=400, detail="Participant does not belong to this meeting")
        
    if rsvp_in.rsvp_status:
        db_p.rsvp_status = rsvp_in.rsvp_status
        
    await db.commit()
    await db.refresh(db_p)
    return db_p


# ==================== AGENDA ENDPOINTS ====================

@router.get("/{meeting_id}/agenda", response_model=AgendaRead)
async def get_meeting_agenda(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the agenda for a specific meeting."""
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(select(Agenda).where(Agenda.meeting_id == meeting_id))
    agenda = result.scalar_one_or_none()
    
    if not agenda:
        raise HTTPException(status_code=404, detail="Agenda not found")
        
    return agenda


@router.post("/{meeting_id}/agenda", response_model=AgendaRead)
async def create_or_update_agenda(
    meeting_id: uuid.UUID,
    agenda_in: AgendaCreate,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """Create or update the agenda for a meeting."""
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(select(Agenda).where(Agenda.meeting_id == meeting_id))
    existing_agenda = result.scalar_one_or_none()
    
    if existing_agenda:
        existing_agenda.content = agenda_in.content
        await db.commit()
        await db.refresh(existing_agenda)
        return existing_agenda
    else:
        db_agenda = Agenda(meeting_id=meeting_id, content=agenda_in.content)
        db.add(db_agenda)
        await db.commit()
        await db.refresh(db_agenda)
        return db_agenda


# ==================== MINUTES ENDPOINTS ====================

@router.get("/{meeting_id}/minutes", response_model=MinutesRead)
async def get_meeting_minutes(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the minutes for a specific meeting."""
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(select(Minutes).where(Minutes.meeting_id == meeting_id))
    minutes = result.scalar_one_or_none()
    
    if not minutes:
        raise HTTPException(status_code=404, detail="Minutes not found")
        
    return minutes


@router.post("/{meeting_id}/minutes", response_model=MinutesRead)
async def create_or_update_minutes(
    meeting_id: uuid.UUID,
    minutes_in: MinutesCreate,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """Create or update the minutes for a meeting."""
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(select(Minutes).where(Minutes.meeting_id == meeting_id))
    existing_minutes = result.scalar_one_or_none()
    
    if existing_minutes:
        existing_minutes.content = minutes_in.content
        if minutes_in.status:
            existing_minutes.status = minutes_in.status
        await db.commit()
        await db.refresh(existing_minutes)
        return existing_minutes
    else:
        db_minutes = Minutes(
            meeting_id=meeting_id,
            content=minutes_in.content,
            status=minutes_in.status if minutes_in.status else MinutesStatus.DRAFT
        )
        db.add(db_minutes)
        await db.commit()
        await db.refresh(db_minutes)
        return db_minutes


# ==================== ACTION ITEMS ENDPOINTS ====================

@router.get("/{meeting_id}/action-items", response_model=List[dict])
async def get_meeting_action_items(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all action items for a specific meeting."""
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(
        select(ActionItem)
        .options(selectinload(ActionItem.owner))
        .where(ActionItem.meeting_id == meeting_id)
    )
    action_items = result.scalars().all()
    
    return [
        {
            "id": str(item.id),
            "description": item.description,
            "owner": {
                "name": item.owner.full_name if item.owner else "Unassigned",
                "avatar": item.owner.full_name[0] if item.owner and item.owner.full_name else "U"
            },
            "dueDate": item.due_date.strftime("%b %d, %Y") if item.due_date else None,
            "status": item.status.value if item.status else "pending"
        }
        for item in action_items
    ]


@router.post("/{meeting_id}/action-items", response_model=dict)
async def create_action_item(
    meeting_id: uuid.UUID,
    action_data: dict,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """Create a new action item for a meeting."""
    from datetime import datetime
    
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    db_action = ActionItem(
        twg_id=db_meeting.twg_id,
        meeting_id=meeting_id,
        description=action_data.get("description"),
        owner_id=uuid.UUID(action_data.get("owner_id")) if action_data.get("owner_id") else current_user.id,
        due_date=datetime.fromisoformat(action_data.get("due_date")) if action_data.get("due_date") else datetime.utcnow(),
        status=action_data.get("status", "PENDING")
    )
    
    db.add(db_action)
    await db.commit()
    await db.refresh(db_action, ["owner"])
    
    return {
        "id": str(db_action.id),
        "description": db_action.description,
        "owner": {
            "name": db_action.owner.full_name if db_action.owner else "Unassigned",
            "avatar": db_action.owner.full_name[0] if db_action.owner and db_action.owner.full_name else "U"
        },
        "dueDate": db_action.due_date.strftime("%b %d, %Y") if db_action.due_date else None,
        "status": db_action.status.value if db_action.status else "pending"
    }


# ==================== DOCUMENTS ENDPOINTS ====================

@router.get("/{meeting_id}/documents", response_model=List[dict])
async def get_meeting_documents(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all documents for a specific meeting."""
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(
        select(Document).where(Document.twg_id == db_meeting.twg_id)
    )
    documents = result.scalars().all()
    
    meeting_docs = [
        doc for doc in documents 
        if doc.metadata_json and doc.metadata_json.get("meeting_id") == str(meeting_id)
    ]
    
    return [
        {
            "id": str(doc.id),
            "file_name": doc.file_name,
            "file_type": doc.file_type,
            "file_size": doc.metadata_json.get("file_size") if doc.metadata_json else None,
            "created_at": doc.created_at.isoformat()
        }
        for doc in meeting_docs
    ]


@router.post("/{meeting_id}/documents")
async def upload_meeting_document(
    meeting_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document for a meeting."""
    import os
    import shutil
    
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    upload_dir = "uploads/meetings"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = os.path.getsize(file_path)
    
    db_document = Document(
        twg_id=db_meeting.twg_id,
        file_name=file.filename,
        file_path=file_path,
        file_type=file.content_type or "application/octet-stream",
        uploaded_by_id=current_user.id,
        metadata_json={
            "meeting_id": str(meeting_id),
            "file_size": file_size
        }
    )
    
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    
    return {
        "id": str(db_document.id),
        "file_name": db_document.file_name,
        "file_type": db_document.file_type,
        "file_size": file_size,
        "created_at": db_document.created_at.isoformat()
    }


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Download a document."""
    from fastapi.responses import FileResponse
    import os
    
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check TWG access
    if document.twg_id and not has_twg_access(current_user, document.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if file exists
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(
        path=document.file_path,
        filename=document.file_name,
        media_type=document.file_type
    )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document."""
    import os
    
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check TWG access
    if document.twg_id and not has_twg_access(current_user, document.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete file from filesystem
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete from database
    await db.delete(document)
    await db.commit()
    
    return {"message": "Document deleted successfully"}

