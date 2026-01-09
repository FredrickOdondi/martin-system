from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.core.database import get_db
from app.models.models import Meeting, Agenda, Minutes, User, UserRole, MinutesStatus, MeetingParticipant, RsvpStatus, ActionItem, TWG, Document, MeetingStatus
from app.schemas.schemas import (
    MeetingCreate, MeetingRead, MeetingUpdate,
    MinutesCreate, MinutesUpdate, MinutesRead,
    AgendaCreate, AgendaRead, AgendaUpdate,
    MeetingParticipantRead, MeetingParticipantUpdate, MeetingParticipantCreate,
    MeetingCancel, MeetingUpdateNotification
)
from app.api.deps import get_current_active_user, require_facilitator, require_twg_access, has_twg_access
from app.services.email_service import email_service
from app.core.config import settings
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
    import traceback
    from datetime import timezone
    from sqlalchemy.orm import selectinload
    try:
        # Check if facilitator has access to this TWG
        if not has_twg_access(current_user, meeting_in.twg_id):
            raise HTTPException(status_code=403, detail="You do not have access to manage meetings for this TWG")

        # Ensure scheduled_at is naive UTC
        if meeting_in.scheduled_at and meeting_in.scheduled_at.tzinfo:
             meeting_in.scheduled_at = meeting_in.scheduled_at.astimezone(timezone.utc).replace(tzinfo=None)

        db_meeting = Meeting(**meeting_in.model_dump())
        db.add(db_meeting)
        await db.commit()
        
        # Eagerly load relationships to avoid MissingGreenlet during serialization
        result = await db.execute(
            select(Meeting)
            .options(selectinload(Meeting.participants))
            .where(Meeting.id == db_meeting.id)
        )
        db_meeting = result.scalar_one()
        return db_meeting
    except Exception as e:
        with open("debug_error.log", "w") as f:
            f.write(traceback.format_exc())
        raise e

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
        selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
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
    
    # Iterate through MeetingParticipant objects
    for participant in db_meeting.participants:
        # Check if registered user
        if participant.user and participant.user.email:
             participant_emails.append(participant.user.email)
        # Check if external guest with email
        elif participant.email:
             participant_emails.append(participant.email)
            
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
                "portal_url": f"{settings.FRONTEND_URL}/schedule"
            },
            meeting_details={
                "title": db_meeting.title,
                "start_time": db_meeting.scheduled_at,
                "duration": db_meeting.duration_minutes,
                "location": db_meeting.location
            }
        )
    except Exception as e:
        # Log full traceback for debugging to stdout for Railway logs
        import traceback
        error_trace = traceback.format_exc()
        print(f"CRITICAL ERROR: Failed to send invitations:\n{error_trace}")
        
        # Also attempt to write to file if possible (fallback)
        try:
            with open("debug_error.log", "w") as f:
                f.write(f"Schedule Meeting Error:\n{error_trace}")
        except:
            pass
            
        raise HTTPException(status_code=500, detail=f"Failed to send invitations: {str(e)}")

    await db.commit()
    return {"status": "successfully scheduled", "emails_sent": len(participant_emails)}


@router.post("/{meeting_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_meeting(
    meeting_id: uuid.UUID,
    cancel_data: MeetingCancel,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a meeting and send cancellation notices with ICS cancellation.
    """
    query = select(Meeting).where(Meeting.id == meeting_id).options(
        selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
        selectinload(Meeting.twg)
    )
    result = await db.execute(query)
    db_meeting = result.scalar_one_or_none()

    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Update status to cancelled
    db_meeting.status = MeetingStatus.CANCELLED
    
    emails_sent = 0
    if cancel_data.notify_participants and db_meeting.participants:
        # Collect emails
        participant_emails = []
        for participant in db_meeting.participants:
            if participant.user and participant.user.email:
                participant_emails.append(participant.user.email)
            elif participant.email:
                participant_emails.append(participant.email)
        
        participant_emails = list(set(participant_emails))

        if participant_emails:
            from app.services.email_service import email_service
            try:
                await email_service.send_meeting_cancellation(
                    to_emails=participant_emails,
                    template_context={
                        "user_name": "Valued Participant",
                        "meeting_title": db_meeting.title,
                        "meeting_date": db_meeting.scheduled_at.strftime("%Y-%m-%d") if db_meeting.scheduled_at else "TBD",
                        "meeting_time": db_meeting.scheduled_at.strftime("%H:%M UTC") if db_meeting.scheduled_at else "TBD",
                        "location": db_meeting.location or "Virtual",
                        "pillar_name": db_meeting.twg.pillar.value if db_meeting.twg else "TWG",
                        "reason": cancel_data.reason,
                        "portal_url": f"{settings.FRONTEND_URL}/schedule"
                    },
                    meeting_details={
                        "title": db_meeting.title,
                        "start_time": db_meeting.scheduled_at or datetime.now(),
                        "duration": db_meeting.duration_minutes,
                        "location": db_meeting.location
                    },
                    reason=cancel_data.reason
                )
                emails_sent = len(participant_emails)
            except Exception as e:
                # Log full traceback for debugging to stdout
                import traceback
                error_trace = traceback.format_exc()
                print(f"CRITICAL ERROR: Failed to send cancellation emails:\n{error_trace}")
                # Don't fail the cancellation just because email failed
                pass

    await db.commit()
    return {"status": "cancelled", "emails_sent": emails_sent}


@router.post("/{meeting_id}/notify-update", status_code=status.HTTP_200_OK)
async def notify_meeting_update(
    meeting_id: uuid.UUID,
    update_data: MeetingUpdateNotification,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Send an update notification to participants with updated ICS details.
    This should be called after modifying meeting details.
    """
    query = select(Meeting).where(Meeting.id == meeting_id).options(
        selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
        selectinload(Meeting.twg)
    )
    result = await db.execute(query)
    db_meeting = result.scalar_one_or_none()

    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")

    emails_sent = 0
    if update_data.notify_participants and db_meeting.participants:
        # Collect emails
        participant_emails = []
        for participant in db_meeting.participants:
            if participant.user and participant.user.email:
                participant_emails.append(participant.user.email)
            elif participant.email:
                participant_emails.append(participant.email)
        
        participant_emails = list(set(participant_emails))

        if participant_emails:
            from app.services.email_service import email_service
            try:
                await email_service.send_meeting_update(
                    to_emails=participant_emails,
                    template_context={
                        "user_name": "Valued Participant",
                        "meeting_title": db_meeting.title,
                        "meeting_date": db_meeting.scheduled_at.strftime("%Y-%m-%d") if db_meeting.scheduled_at else "TBD",
                        "meeting_time": db_meeting.scheduled_at.strftime("%H:%M UTC") if db_meeting.scheduled_at else "TBD",
                        "location": db_meeting.location or "Virtual",
                        "pillar_name": db_meeting.twg.pillar.value if db_meeting.twg else "TWG",
                        "changes": update_data.changes,
                        "portal_url": f"{settings.FRONTEND_URL}/schedule"
                    },
                    meeting_details={
                        "title": db_meeting.title,
                        "start_time": db_meeting.scheduled_at or datetime.now(),
                        "duration": db_meeting.duration_minutes,
                        "location": db_meeting.location
                    },
                    changes=update_data.changes
                )
                emails_sent = len(participant_emails)
            except Exception as e:
                # Log full traceback for debugging to stdout
                import traceback
                error_trace = traceback.format_exc()
                print(f"CRITICAL ERROR: Failed to send update emails:\n{error_trace}")
                # Raise warning but don't strictly crash 500 if we want to be lenient,
                # BUT since this endpoint is *only* for notification, a failure IS an error.
                # Use 500 but log it properly so user sees it in Railway.
                raise HTTPException(status_code=500, detail=f"Failed to send update emails: {str(e)}")

    return {"status": "notification_sent", "emails_sent": emails_sent}


@router.post("/{meeting_id}/conflict-check")
async def check_meeting_conflicts(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check for scheduling conflicts before sending invites.
    Scans for:
    - VIP double-bookings (same participant in two meetings at same time)
    - Venue conflicts (same location booked at same time)
    - TWG member overlaps (key members in conflicting meetings)
    
    This is the Supervisor Agent's "Air Traffic Control" function.
    """
    from datetime import timedelta
    
    # Get the meeting with participants
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
            selectinload(Meeting.twg)
        )
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if meeting has a scheduled time
    if not db_meeting.scheduled_at:
        return {
            "meeting_id": str(meeting_id),
            "conflicts": [],
            "has_conflicts": False,
            "can_proceed": True,
            "message": "Meeting has no scheduled time - skipping conflict check"
        }
    
    conflicts = []
    meeting_start = db_meeting.scheduled_at
    meeting_end = meeting_start + timedelta(minutes=db_meeting.duration_minutes or 60)
    
    # Get all other meetings that overlap in time
    overlapping_query = select(Meeting).options(
        selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
        selectinload(Meeting.twg)
    ).where(
        Meeting.id != meeting_id,
        Meeting.scheduled_at < meeting_end,
        (Meeting.scheduled_at + timedelta(minutes=60)) > meeting_start  # Approximate end time
    )
    
    overlapping_result = await db.execute(overlapping_query)
    overlapping_meetings = overlapping_result.scalars().all()
    
    # Build list of participant emails/IDs for this meeting
    this_meeting_participants = set()
    for p in db_meeting.participants:
        if p.user_id:
            this_meeting_participants.add(str(p.user_id))
        if p.email:
            this_meeting_participants.add(p.email.lower())
    
    for other_meeting in overlapping_meetings:
        # Check 1: Venue conflicts
        if db_meeting.location and other_meeting.location:
            if db_meeting.location.lower().strip() == other_meeting.location.lower().strip():
                conflicts.append({
                    "type": "venue_conflict",
                    "severity": "high",
                    "message": f"Venue '{db_meeting.location}' is already booked",
                    "conflicting_meeting": {
                        "id": str(other_meeting.id),
                        "title": other_meeting.title,
                        "time": other_meeting.scheduled_at.isoformat() if other_meeting.scheduled_at else None,
                        "twg": other_meeting.twg.name if other_meeting.twg else None
                    }
                })
        
        # Check 2: Participant double-booking
        other_participants = set()
        for p in other_meeting.participants:
            if p.user_id:
                other_participants.add(str(p.user_id))
            if p.email:
                other_participants.add(p.email.lower())
        
        overlapping_people = this_meeting_participants & other_participants
        if overlapping_people:
            # Determine if any are VIPs (for now, treat all as important)
            for person_id in overlapping_people:
                # Try to find the name
                person_name = person_id
                for p in db_meeting.participants:
                    if str(p.user_id) == person_id or (p.email and p.email.lower() == person_id):
                        person_name = p.user.full_name if p.user else (p.name or p.email)
                        break
                
                conflicts.append({
                    "type": "participant_conflict",
                    "severity": "high",
                    "message": f"'{person_name}' is scheduled for another meeting at this time",
                    "conflicting_meeting": {
                        "id": str(other_meeting.id),
                        "title": other_meeting.title,
                        "time": other_meeting.scheduled_at.isoformat() if other_meeting.scheduled_at else None,
                        "twg": other_meeting.twg.name if other_meeting.twg else None
                    }
                })
    
    return {
        "meeting_id": str(meeting_id),
        "conflicts": conflicts,
        "has_conflicts": len(conflicts) > 0,
        "can_proceed": True,  # Allow override with acknowledgment
        "message": f"Found {len(conflicts)} potential conflict(s)" if conflicts else "No conflicts detected"
    }

@router.post("/{meeting_id}/participants", response_model=List[MeetingParticipantRead])
async def add_participants(
    meeting_id: uuid.UUID,
    participants: List[MeetingParticipantCreate],
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Add participants (users or external guests) to a meeting.
    """
    # Verify meeting exists
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")

    new_participants = []
    
    for p_in in participants:
         # logic to check duplicates could go here
         
         db_p = MeetingParticipant(
             meeting_id=meeting_id,
             user_id=p_in.user_id,
             email=p_in.email,
             name=p_in.name,
             rsvp_status=RsvpStatus.PENDING
         )
         db.add(db_p)
         new_participants.append(db_p)
         
    await db.commit()
    
    # Refresh to return
    for p in new_participants:
        await db.refresh(p)
        
    return new_participants

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


@router.post("/{meeting_id}/agenda/generate")
async def generate_agenda(
    meeting_id: uuid.UUID,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a draft agenda using the Supervisor AI agent.
    The Supervisor coordinates the specific TWG agent to draft the content.
    """
    from app.agents.langgraph_base_agent import create_langgraph_agent
    
    # Get meeting with TWG info
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.twg))
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Use Supervisor Agent ("Secretariat AI")
    agent = create_langgraph_agent(agent_id="supervisor", session_id=str(meeting_id))
    
    pillar_name = db_meeting.twg.pillar.value if db_meeting.twg else "Unspecified"
    
    # Prompt Supervisor to coordinate the task
    prompt = f"""Act as the Summit Secretariat Supervisor. Instruct the {pillar_name} TWG Agent to draft a professional meeting agenda for the following session.

Meeting Details:
- Title: {db_meeting.title}
- Date: {db_meeting.scheduled_at.strftime('%Y-%m-%d %H:%M UTC') if db_meeting.scheduled_at else 'TBD'}
- Duration: {db_meeting.duration_minutes} minutes
- Location: {db_meeting.location or 'Virtual'}
- TWG Pillar: {pillar_name}

INSTRUCTIONS:
1. Generate the agenda CONTENT ONLY.
2. Use the strict MARKDOWN structure below.
3. DO NOT include any conversational text (e.g., "Here is the agenda...").
4. DO NOT simulate sending emails or calling tools.
5. The output must be PURE MARKDOWN.

STRUCTURE:

# Meeting Agenda: {db_meeting.title}

## 1. Opening & Welcome (5 min)
- Introduction by the Chair
- Meeting objectives overview

## 2. Review of Previous Action Items (10 min)
- Status updates
- Outstanding items

## 3. Main Discussion Topics
Discussion topics relevant to the {pillar_name} pillar:
- **Topic 1**: [description based on context]
- **Topic 2**: [description based on context]

## 4. Action Items & Next Steps
- New assignments
- Deadlines

## 5. Closing Remarks (5 min)
- Summary
- Adjournment"""

    generated_content = agent.chat(prompt)
    
    return {"generated_agenda": generated_content}


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


@router.post("/{meeting_id}/minutes/generate")
async def generate_minutes(
    meeting_id: uuid.UUID,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate draft meeting minutes using the Supervisor AI agent.
    The Supervisor coordinates the specific TWG agent (Rapporteur Mode) to draft the minutes.
    """
    from app.agents.langgraph_base_agent import create_langgraph_agent
    
    # Get meeting with TWG and agenda info
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.twg), selectinload(Meeting.agenda))
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Use Supervisor Agent ("Secretariat AI")
    agent = create_langgraph_agent(agent_id="supervisor", session_id=str(meeting_id))
    
    pillar_name = db_meeting.twg.pillar.value if db_meeting.twg else "Unspecified"
    
    # Use transcript if available, otherwise use agenda
    context = db_meeting.transcript if db_meeting.transcript else ""
    agenda_content = db_meeting.agenda.content if db_meeting.agenda else ""
    
    prompt = f"""Act as the Summit Secretariat Supervisor. Instruct the {pillar_name} TWG Agent to draft professional meeting minutes for the following session.

Meeting Details:
- Title: {db_meeting.title}
- Date: {db_meeting.scheduled_at.strftime('%Y-%m-%d %H:%M UTC') if db_meeting.scheduled_at else 'TBD'}
- Duration: {db_meeting.duration_minutes} minutes
- Location: {db_meeting.location or 'Virtual'}
- TWG Pillar: {pillar_name}

Context (Agenda/Transcript):
{agenda_content}

{f"Transcript/Notes:{chr(10)}{context}" if context else "No transcript available - generate based on typical ECOWAS TWG proceedings."}

INSTRUCTIONS:
1. Generate the minutes CONTENT ONLY.
2. Use the strict MARKDOWN structure below.
3. DO NOT include any conversational text (e.g., "Here are the minutes...").
4. DO NOT simulate sending emails or calling tools.
5. The output must be PURE MARKDOWN.

STRUCTURE:

# ECOWAS Technical Working Group Meeting Minutes

## Meeting Details
- **Title:** [title]
- **Date:** [date]
- **Location:** [location]
- **Attendees:** [placeholder]

## Opening and Welcome
[Opening remarks]

## Discussion Points
1. **[Topic 1]**: [description]
2. **[Topic 2]**: [description]

## Key Decisions
1. [Decision 1]
2. [Decision 2]

## Action Items
| Owner | Task | Due Date |
|-------|------|----------|
| TBD | [task] | [date] |

## Next Steps
[Next steps]

## Closing
[Closing remarks]"""

    generated_content = agent.chat(prompt)
    
    return {"generated_minutes": generated_content}


@router.post("/{meeting_id}/minutes/submit-for-approval")
async def submit_minutes_for_approval(
    meeting_id: uuid.UUID,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit minutes for approval. Changes status from DRAFT to PENDING_APPROVAL.
    Human oversight gate: Nothing is finalized until explicitly approved.
    """
    # Get meeting and minutes
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.minutes))
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not db_meeting.minutes:
        raise HTTPException(status_code=400, detail="No minutes to submit")
    
    if db_meeting.minutes.status != MinutesStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Minutes must be in DRAFT status to submit. Current: {db_meeting.minutes.status.value}")
    
    # Update status
    db_meeting.minutes.status = MinutesStatus.PENDING_APPROVAL
    await db.commit()
    await db.refresh(db_meeting.minutes)
    
    return {
        "message": "Minutes submitted for approval",
        "status": db_meeting.minutes.status.value,
        "meeting_id": str(meeting_id)
    }


@router.post("/{meeting_id}/minutes/approve")
async def approve_minutes(
    meeting_id: uuid.UUID,
    current_user: User = Depends(require_facilitator),  # Could be require_admin for stricter control
    db: AsyncSession = Depends(get_db)
):
    """
    Approve minutes. Changes status from PENDING_APPROVAL to APPROVED.
    This is the human oversight gate - nothing is official until approved.
    """
    # Get meeting and minutes
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.minutes))
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not db_meeting.minutes:
        raise HTTPException(status_code=400, detail="No minutes to approve")
    
    if db_meeting.minutes.status != MinutesStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail=f"Minutes must be PENDING_APPROVAL to approve. Current: {db_meeting.minutes.status.value}")
    
    # Approve
    db_meeting.minutes.status = MinutesStatus.APPROVED
    await db.commit()
    await db.refresh(db_meeting.minutes)
    
    # TODO: Optionally send notification email to participants
    
    return {
        "message": "Minutes approved",
        "status": db_meeting.minutes.status.value,
        "meeting_id": str(meeting_id),
        "approved_by": current_user.full_name
    }


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


@router.post("/{meeting_id}/extract-actions")
async def extract_action_items(
    meeting_id: uuid.UUID,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Use AI to extract action items from meeting minutes and create ActionItem records.
    """
    from app.agents.langgraph_base_agent import create_langgraph_agent
    import json
    import re
    
    # Get meeting with minutes
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.twg), selectinload(Meeting.minutes))
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    minutes_content = ""
    if db_meeting.minutes:
        minutes_content = db_meeting.minutes.content
    elif db_meeting.transcript:
        minutes_content = db_meeting.transcript
    
    if not minutes_content:
        raise HTTPException(status_code=400, detail="No minutes or transcript available to extract actions from")
    
    # Create agent to extract action items
    pillar = db_meeting.twg.pillar.value if db_meeting.twg else "energy_infrastructure"
    agent_id = pillar.split("_")[0]
    agent = create_langgraph_agent(agent_id=agent_id, session_id=str(meeting_id))
    
    prompt = f"""Extract action items from the following meeting minutes.

Meeting: {db_meeting.title}

Minutes:
{minutes_content}

Return ONLY a JSON array of action items, each with:
- "description": the action item text
- "owner": suggested owner name (or "TBD" if unclear)
- "due_date": suggested due date in YYYY-MM-DD format (or null if unclear)

Example format:
[
  {{"description": "Draft energy policy framework", "owner": "TBD", "due_date": "2026-02-01"}},
  {{"description": "Review ECOWAS Vision 2050 alignment", "owner": "TBD", "due_date": null}}
]

Return ONLY valid JSON, no markdown or other text."""

    response = agent.chat(prompt)
    
    # Parse the JSON from response
    try:
        # Try to find JSON array in the response
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            extracted_items = json.loads(json_match.group())
        else:
            extracted_items = json.loads(response)
    except json.JSONDecodeError:
        return {"extracted_actions": [], "raw_response": response, "error": "Could not parse JSON"}
    
    # Auto-create ActionItem records
    created_items = []
    for item in extracted_items:
        try:
            from datetime import datetime, timedelta
            
            # Parse due date or default to 2 weeks from now
            due_date = None
            if item.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(item["due_date"])
                except:
                    due_date = datetime.utcnow() + timedelta(days=14)
            else:
                due_date = datetime.utcnow() + timedelta(days=14)
            
            db_action = ActionItem(
                twg_id=db_meeting.twg_id,
                meeting_id=meeting_id,
                description=item.get("description", ""),
                owner_id=current_user.id,  # Default to current user, can be reassigned
                due_date=due_date,
                status="PENDING"
            )
            db.add(db_action)
            created_items.append({
                "description": item.get("description"),
                "owner": item.get("owner", "TBD"),
                "due_date": due_date.isoformat() if due_date else None,
                "created": True
            })
        except Exception as e:
            created_items.append({
                "description": item.get("description"),
                "error": str(e),
                "created": False
            })
    
    await db.commit()
    
    return {
        "extracted_actions": extracted_items,
        "created_items": created_items,
        "meeting_id": str(meeting_id),
        "message": f"Created {len([i for i in created_items if i.get('created')])} action items"
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


# ==================== MEETING PACK ENDPOINTS ====================

@router.post("/{meeting_id}/meeting-pack")
async def compile_meeting_pack(
    meeting_id: uuid.UUID,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Compile a meeting pack containing:
    1. Agenda PDF (on summit letterhead)
    2. Previous meeting minutes (if available)
    3. Attached pre-read documents
    
    Returns a ZIP file with all materials.
    """
    import zipfile
    import io
    import os
    from fastapi.responses import StreamingResponse
    from app.services.format_service import format_service
    
    # Get meeting with all related data
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.twg),
            selectinload(Meeting.agenda),
            selectinload(Meeting.minutes)
        )
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create ZIP buffer
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        files_added = []
        
        # 1. Generate Agenda PDF with letterhead
        if db_meeting.agenda and db_meeting.agenda.content:
            pillar = db_meeting.twg.pillar.value if db_meeting.twg else "energy_infrastructure"
            
            pdf_bytes, pdf_filename = format_service.generate_agenda_pdf(
                twg_pillar=pillar,
                meeting_title=db_meeting.title,
                meeting_date=db_meeting.scheduled_at,
                meeting_location=db_meeting.location or "Virtual",
                agenda_content=db_meeting.agenda.content,
                duration_minutes=db_meeting.duration_minutes
            )
            
            zip_file.writestr(pdf_filename, pdf_bytes)
            files_added.append(pdf_filename)
        
        # 2. Get previous meeting minutes (if any exist for this TWG)
        prev_meetings_result = await db.execute(
            select(Meeting)
            .options(selectinload(Meeting.minutes))
            .where(
                Meeting.twg_id == db_meeting.twg_id,
                Meeting.scheduled_at < db_meeting.scheduled_at,
                Meeting.id != db_meeting.id
            )
            .order_by(Meeting.scheduled_at.desc())
            .limit(1)
        )
        prev_meeting = prev_meetings_result.scalar_one_or_none()
        
        if prev_meeting and prev_meeting.minutes and prev_meeting.minutes.content:
            prev_date = prev_meeting.scheduled_at.strftime('%Y-%m-%d') if prev_meeting.scheduled_at else "previous"
            pillar_short = db_meeting.twg.pillar.value.split("_")[0].title() if db_meeting.twg else "TWG"
            minutes_filename = f"{pillar_short}TWG_Minutes_{prev_date}.txt"
            zip_file.writestr(minutes_filename, prev_meeting.minutes.content)
            files_added.append(minutes_filename)
        
        # 3. Get attached documents for this meeting
        docs_result = await db.execute(
            select(Document).where(Document.twg_id == db_meeting.twg_id)
        )
        documents = docs_result.scalars().all()
        
        for doc in documents[:5]:  # Limit to 5 pre-read docs
            if os.path.exists(doc.file_path):
                with open(doc.file_path, 'rb') as f:
                    zip_file.writestr(f"prereads/{doc.file_name}", f.read())
                    files_added.append(f"prereads/{doc.file_name}")
    
    zip_buffer.seek(0)
    
    # Generate pack filename
    pillar_short = db_meeting.twg.pillar.value.split("_")[0].title() if db_meeting.twg else "TWG"
    date_str = db_meeting.scheduled_at.strftime('%Y-%m-%d') if db_meeting.scheduled_at else "draft"
    pack_filename = f"{pillar_short}TWG_MeetingPack_{date_str}.zip"
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={pack_filename}"}
    )


# ==================== NEXT-MEETING AUTOMATION ====================

@router.post("/{meeting_id}/propose-next")
async def propose_next_meeting(
    meeting_id: uuid.UUID,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Use AI to propose the next meeting date based on:
    - Current meeting date
    - TWG's typical cadence (defaults to bi-weekly)
    - Avoids weekends
    
    Optionally creates a draft meeting record.
    """
    from datetime import timedelta
    from app.agents.langgraph_base_agent import create_langgraph_agent
    
    # Get current meeting
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.twg))
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate proposed date (default: 2 weeks from current meeting)
    current_date = db_meeting.scheduled_at
    proposed_date = current_date + timedelta(weeks=2)
    
    # Adjust to avoid weekends (push to Monday if needed)
    while proposed_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        proposed_date += timedelta(days=1)
    
    # Get AI to suggest title and confirm
    pillar = db_meeting.twg.pillar.value if db_meeting.twg else "energy_infrastructure"
    agent_id = pillar.split("_")[0]
    agent = create_langgraph_agent(agent_id=agent_id, session_id=str(meeting_id))
    
    prompt = f"""Based on the previous meeting titled "{db_meeting.title}" for the {pillar.replace('_', ' ').title()} TWG, 
suggest a concise title for the follow-up meeting scheduled for {proposed_date.strftime('%A, %d %B %Y')}.

Return only the meeting title, nothing else. Keep it under 80 characters.
Example: "Energy TWG Session 2: Infrastructure Assessment Review"
"""
    
    suggested_title = agent.chat(prompt).strip().strip('"')
    
    # Create draft meeting (status will be SCHEDULED by default, but not yet finalized)
    draft_meeting = Meeting(
        twg_id=db_meeting.twg_id,
        title=suggested_title or f"Follow-up: {db_meeting.title}",
        scheduled_at=proposed_date,
        duration_minutes=db_meeting.duration_minutes,
        location=db_meeting.location,
        status=MeetingStatus.SCHEDULED,
        meeting_type=db_meeting.meeting_type
    )
    db.add(draft_meeting)
    await db.commit()
    await db.refresh(draft_meeting)
    
    return {
        "proposed_date": proposed_date.isoformat(),
        "proposed_title": suggested_title or f"Follow-up: {db_meeting.title}",
        "draft_meeting_id": str(draft_meeting.id),
        "message": "Draft meeting created. Review and finalize using the scheduling endpoint.",
        "based_on_meeting": str(meeting_id)
    }
