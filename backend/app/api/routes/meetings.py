from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, WebSocket
from app.services.audit_service import audit_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
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
from app.services.document_synthesizer import DocumentSynthesizer
from app.services.llm_service import llm_service

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

        # GENERATE GOOGLE MEET LINK
        # Only if configured and virtual
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"CREATE_MEETING: meeting_type='{meeting_in.meeting_type}'")
        
        # Generate ID explicitly so we can link it in GCal
        meeting_id = uuid.uuid4()
        
        generated_video_link = None
        if meeting_in.meeting_type == "virtual":
            logger.warning("CREATE_MEETING: Entering virtual meeting block")
            try:
                from app.services.calendar_service import calendar_service
                calendar_event = calendar_service.create_meeting_event(
                    title=meeting_in.title,
                    start_time=meeting_in.scheduled_at,
                    duration_minutes=meeting_in.duration_minutes,
                    description=f"Automated meeting for TWG: {meeting_in.twg_id}",
                    attendees=[],
                    meeting_id=str(meeting_id)
                )
                if calendar_event.get('hangoutLink'):
                     logger.warning(f"CREATE_MEETING: Generated link: {calendar_event.get('hangoutLink')}")
                     generated_video_link = calendar_event.get('hangoutLink')
                else:
                     logger.warning(f"CREATE_MEETING: Event created but NO link found")
            except Exception as e:
                # Log detailed error but DO NOT fail the meeting creation
                logger.error(f"CREATE_MEETING: Failed to generate Meet link: {e}")
                # If it's an HttpError, it might be the 'Invalid conference type value'
                # causing issues with service accounts. We proceed without video link.

        # Create meeting with video_link
        meeting_data = meeting_in.model_dump()
        meeting_data['id'] = meeting_id
        meeting_data['video_link'] = generated_video_link
        db_meeting = Meeting(**meeting_data)
        db.add(db_meeting)
        await db.commit()
        
        # Eagerly load relationships to avoid MissingGreenlet during serialization
        # Eagerly load relationships to avoid MissingGreenlet during serialization
        result = await db.execute(
            select(Meeting)
            .options(
                selectinload(Meeting.participants),
                selectinload(Meeting.documents), # Added to satisfy MeetingRead schema
                selectinload(Meeting.twg)        # Good practice to include parent
            )
            .where(Meeting.id == db_meeting.id)
        )
        db_meeting = result.scalar_one()
        return db_meeting
    except Exception as e:
        logger.error(f"CREATE_MEETING FAILED: {str(e)}") # Improved logging
        import traceback
        traceback.print_exc()
        raise e

@router.get("/", response_model=List[MeetingRead])
async def list_meetings(
    skip: int = 0,
    limit: int = 100,
    twg_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all meetings visible to the user.
    """
    # If admin, show all (unless filtered). If member, show only their TWG meetings.
    query = select(Meeting).offset(skip).limit(limit)
    
    if twg_id:
        if not has_twg_access(current_user, twg_id):
             raise HTTPException(status_code=403, detail="Access denied to this TWG")
        query = query.where(Meeting.twg_id == twg_id)
    elif current_user.role not in [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD]:
        # Get IDs of TWGs user belongs to
        user_twg_ids = [twg.id for twg in current_user.twgs]
        query = query.where(Meeting.twg_id.in_(user_twg_ids))
        
    query = query.options(
        selectinload(Meeting.participants).selectinload(MeetingParticipant.user), # Fix for 500 error
        selectinload(Meeting.twg),
        selectinload(Meeting.documents).selectinload(Document.uploaded_by),
        selectinload(Meeting.documents).selectinload(Document.twg)
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
    print(f"DEBUG: get_meeting called for {meeting_id}")
    query = select(Meeting).where(Meeting.id == meeting_id).options(
        selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
        selectinload(Meeting.agenda),
        selectinload(Meeting.minutes),
        selectinload(Meeting.twg),
        selectinload(Meeting.documents)
    )
    result = await db.execute(query)
    db_meeting = result.scalar_one_or_none()
    print(f"DEBUG: get_meeting loaded: {db_meeting is not None}")
    if db_meeting:
        print(f"DEBUG: minutes loaded: {db_meeting.minutes}")
        print(f"DEBUG: documents count: {len(db_meeting.documents)}")
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
    query = select(Meeting).where(Meeting.id == meeting_id).options(
        selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
        selectinload(Meeting.twg),
        selectinload(Meeting.agenda)
    )
    result = await db.execute(query)
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

@router.post("/{meeting_id}/generate-minutes", response_model=MinutesRead)
async def generate_minutes(
    meeting_id: uuid.UUID,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate 'Zero Draft' minutes from the meeting transcript using AI.
    """
    # 1. Fetch Meeting with all context
    query = select(Meeting).where(Meeting.id == meeting_id).options(
        selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
        selectinload(Meeting.agenda),
        selectinload(Meeting.twg)
    )
    result = await db.execute(query)
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # 2. Validation
    if not db_meeting.transcript:
        raise HTTPException(status_code=400, detail="No transcript available for this meeting. Please add a transcript first.")

    # 3. Prepare Context for Synthesizer
    attendees_list = []
    for p in db_meeting.participants:
        name = p.user.full_name if (p.user and p.user.full_name) else (p.name or p.email or "Unknown")
        role = f" ({p.user.role.value})" if (p.user and p.user.role) else ""
        attendees_list.append(f"- {name}{role}")
    
    meeting_context = {
        "meeting_title": db_meeting.title,
        "meeting_date": db_meeting.scheduled_at.strftime("%Y-%m-%d"),
        "pillar_name": db_meeting.twg.pillar.value if db_meeting.twg else "General",
        "attendees_list": "\n".join(attendees_list),
        "agenda_content": db_meeting.agenda.content if db_meeting.agenda else "No formal agenda provided."
    }

    # 4. Generate Minutes
    synthesizer = DocumentSynthesizer(llm_client=llm_service)
    try:
        minutes_result = synthesizer.synthesize_minutes(
            transcript_text=db_meeting.transcript,
            meeting_context=meeting_context
        )
        generated_content = minutes_result["content"]
        
        # 5. Save to DB (Upsert)
        # Check for existing minutes
        min_result = await db.execute(select(Minutes).where(Minutes.meeting_id == meeting_id))
        db_minutes = min_result.scalar_one_or_none()
        
        if db_minutes:
             db_minutes.content = generated_content
             # Keep status as whatever it was, or reset to DRAFT? Usually reset to DRAFT if re-generated.
             db_minutes.status = MinutesStatus.DRAFT
        else:
            db_minutes = Minutes(
                meeting_id=meeting_id,
                content=generated_content,
                status=MinutesStatus.DRAFT
            )
            db.add(db_minutes)
            
        # Log activity
        await audit_service.log_activity(
            db=db,
            user_id=current_user.id,
            action="MINUTES_GENERATED",
            resource_type="meeting",
            resource_id=meeting_id,
            details={"transcript_length": len(db_meeting.transcript)}
        )
        
        await db.commit()
        await db.refresh(db_minutes)
        return db_minutes

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate minutes: {str(e)}")


@router.post("/{meeting_id}/upload-recording", response_model=MinutesRead)
async def upload_recording(
    meeting_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an audio recording, transcribe it using Groq Whisper, saving the transcript,
    and then automatically generate minutes.
    """
    import shutil
    import os
    from app.core.config import settings
    
    # 1. Validation
    if not file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm')):
        raise HTTPException(status_code=400, detail="Invalid file format. Supported: mp3, wav, m4a, mp4, mpeg, mpga, webm")

    # 2. Save File Temporarily
    upload_dir = os.path.join(settings.UPLOAD_DIR, "recordings")
    os.makedirs(upload_dir, exist_ok=True)
    temp_file_path = os.path.join(upload_dir, f"{meeting_id}_{file.filename}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        print(f"File saved to {temp_file_path}, starting transcription...")

        # 3. Transcribe using LLM Service (Groq)
        try:
            transcript_text = llm_service.transcribe_audio(temp_file_path)
        except NotImplementedError:
             raise HTTPException(status_code=500, detail="Audio transcription is not supported by the current LLM provider configuration.")
        
        print(f"Transcription complete. Length: {len(transcript_text)}")

        # 4. Update Meeting Transcript in DB
        result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
        db_meeting = result.scalar_one_or_none()
        
        if not db_meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
            
        if not has_twg_access(current_user, db_meeting.twg_id):
             raise HTTPException(status_code=403, detail="Access denied")

        db_meeting.transcript = transcript_text
        await db.commit()
        
        # 5. Trigger Minute Generation (Reuse logic)
        # We can call the generate_minutes endpoint handler directly or reuse the logic.
        # Calling handler directly is tricky due to Dependency Injection.
        # Better to reuse the service logic.
        
        # Re-fetch with full relationships for context
        query = select(Meeting).where(Meeting.id == meeting_id).options(
            selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
            selectinload(Meeting.agenda),
            selectinload(Meeting.twg)
        )
        result = await db.execute(query)
        db_meeting = result.scalar_one_or_none()
        
        attendees_list = []
        for p in db_meeting.participants:
            name = p.user.full_name if (p.user and p.user.full_name) else (p.name or p.email or "Unknown")
            role = f" ({p.user.role.value})" if (p.user and p.user.role) else ""
            attendees_list.append(f"- {name}{role}")
        
        meeting_context = {
            "meeting_title": db_meeting.title,
            "meeting_date": db_meeting.scheduled_at.strftime("%Y-%m-%d"),
            "pillar_name": db_meeting.twg.pillar.value if db_meeting.twg else "General",
            "attendees_list": "\n".join(attendees_list),
            "agenda_content": db_meeting.agenda.content if db_meeting.agenda else "No formal agenda provided."
        }

        synthesizer = DocumentSynthesizer(llm_client=llm_service)
        minutes_result = synthesizer.synthesize_minutes(
             transcript_text=db_meeting.transcript,
             meeting_context=meeting_context
        )
        generated_content = minutes_result["content"]
        
        # Upsert Minutes
        min_result = await db.execute(select(Minutes).where(Minutes.meeting_id == meeting_id))
        db_minutes = min_result.scalar_one_or_none()
        
        if db_minutes:
             db_minutes.content = generated_content
             db_minutes.status = MinutesStatus.DRAFT
        else:
            db_minutes = Minutes(
                meeting_id=meeting_id,
                content=generated_content,
                status=MinutesStatus.DRAFT
            )
            db.add(db_minutes)
            
        await db.commit()
        await db.refresh(db_minutes)
        
        # Cleanup
        if os.path.exists(temp_file_path):
             os.remove(temp_file_path)

        return db_minutes

    except Exception as e:
        # Cleanup on error
        if os.path.exists(temp_file_path):
             os.remove(temp_file_path)
        import traceback
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process recording: {str(e)}")

@router.websocket("/{meeting_id}/live")
async def live_meeting_transcription_websocket(
    websocket: WebSocket, 
    meeting_id: uuid.UUID,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    from app.services.speech_service import speech_service
    from app.utils.security import verify_token
    import asyncio
    import time
    from fastapi import WebSocketDisconnect
    from app.models.models import Agenda
    from app.agents.agenda_monitor import AgendaMonitor
    
    # 1. Connection & Auth
    await websocket.accept()
    
    user_id = "anonymous"
    if token:
        payload = verify_token(token, "access")
        if payload:
            user_id = payload.get("sub")
    
    print(f"WS Connected to Meeting {meeting_id} | User: {user_id}")
    
    # Fetch Agenda for Context
    result = await db.execute(select(Agenda).where(Agenda.meeting_id == meeting_id))
    agenda = result.scalar_one_or_none()
    agenda_text = agenda.content if agenda else "No agenda content available."

    # Init Agent
    monitor = AgendaMonitor()
    transcript_buffer = ""
    last_analysis_time = time.time()

    # Async Queue to buffer audio chunks from Client -> Google
    audio_queue = asyncio.Queue()
    
    async def receive_audio():
        """Reads audio chunks from WebSocket and puts into queue."""
        try:
            while True:
                data = await websocket.receive_bytes()
                await audio_queue.put(data)
        except WebSocketDisconnect:
             await audio_queue.put(None)
        except Exception as e:
            print(f"Receive Error: {e}")
            await audio_queue.put(None) # Signal EOF

    async def audio_generator():
        """Yields chunks from queue to Google Speech Service."""
        while True:
            chunk = await audio_queue.get()
            if chunk is None:
                break
            yield chunk

    # 3. Main Loop
    try:
        # Start receiver task
        receiver_task = asyncio.create_task(receive_audio())
        
        # Start Google Stream (Bi-directional)
        async for transcript_data in speech_service.stream_audio(audio_generator()):
            # 1. Send Transcript
            await websocket.send_json({
                "type": "transcript",
                "data": transcript_data
            })
            
            # 2. Agenda Monitor Analysis
            # Only analyze "final" results to save tokens/stability
            if transcript_data.get('is_final'):
                new_text = transcript_data.get('text', '')
                transcript_buffer += " " + new_text
                
                # Check triggers (Time + buffer size)
                # Analyze every 15 seconds if there is new content
                if time.time() - last_analysis_time > 15 and len(new_text) > 10:
                    print(f"Running Agenda Monitor Analysis... Buffer: {len(transcript_buffer)}")
                    analysis = await monitor.analyze(transcript_buffer, agenda_text)
                    
                    if analysis:
                        await websocket.send_json({
                            "type": "agenda_update",
                            "data": analysis
                        })
                    
                    last_analysis_time = time.time()
                    
                    # Manage Buffer Size (keep context but don't explode)
                    if len(transcript_buffer) > 4000:
                        transcript_buffer = transcript_buffer[-2000:]
            
    except Exception as e:
        print(f"WebSocket Error: {e}")
        try:
             await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
        print(f"WS Closed for Meeting {meeting_id}")

@router.get("/{meeting_id}/invite-preview")
async def get_invite_preview(
    meeting_id: uuid.UUID,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a preview of the meeting invitation email and participant list.
    This allows the facilitator to review before approving.
    """
    from app.schemas.schemas import InvitePreview, InviteStatus
    
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

    # Collect participant emails
    participant_emails = []
    for participant in db_meeting.participants:
        if participant.user and participant.user.email:
            participant_emails.append(participant.user.email)
        elif participant.email:
            participant_emails.append(participant.email)
    participant_emails = list(set(participant_emails))

    # Render email template for preview
    template_context = {
        "user_name": "Valued Participant",
        "meeting_title": db_meeting.title,
        "meeting_date": db_meeting.scheduled_at.strftime("%Y-%m-%d") if db_meeting.scheduled_at else "TBD",
        "meeting_time": db_meeting.scheduled_at.strftime("%H:%M UTC") if db_meeting.scheduled_at else "TBD",
        "location": db_meeting.location or "Virtual",
        "video_link": db_meeting.video_link,
        "pillar_name": db_meeting.twg.pillar.value if db_meeting.twg else "TWG",
        "portal_url": f"{settings.FRONTEND_URL}/schedule"
    }
    
    # Render the template
    try:
        template = email_service.jinja_env.get_template("meeting_invite.html")
        html_content = template.render(**template_context)
    except Exception as e:
        html_content = f"<p>Template rendering failed: {str(e)}</p>"

    # Determine status
    status = InviteStatus.SENT if db_meeting.status == MeetingStatus.SCHEDULED else InviteStatus.DRAFT

    return InvitePreview(
        meeting_id=meeting_id,
        subject=f"INVITATION: {db_meeting.title}",
        html_content=html_content,
        participants=participant_emails,
        ics_attached=True,
        status=status
    )


@router.post("/{meeting_id}/schedule", status_code=status.HTTP_200_OK)
async def schedule_meeting_draft(
    meeting_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a meeting as ready to schedule (DRAFT state).
    Does NOT send emails - use /approve-invite after reviewing the preview.
    """
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

    # Don't change status yet - wait for approval
    # Just return the preview info
    participant_count = len(db_meeting.participants)

    # Log activity
    await audit_service.log_activity(
        db=db,
        user_id=current_user.id,
        action="MEETING_DRAFT_CREATED",
        resource_type="meeting",
        resource_id=meeting_id,
        details={"status": "draft_ready", "participant_count": participant_count},
        ip_address=request.client.host if request.client else None
    )

    return {
        "status": "ready_for_approval",
        "message": "Please review the invite preview and click 'Approve & Send' to dispatch invitations.",
        "participant_count": participant_count
    }


@router.post("/{meeting_id}/approve-invite", status_code=status.HTTP_200_OK)
async def approve_and_send_invite(
    meeting_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    HITL Approval Gate: Actually send the meeting invitations after human review.
    This is the final step that dispatches emails to participants.
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

    if not db_meeting.participants:
        raise HTTPException(status_code=400, detail="No participants assigned to this meeting")

    # Mark as scheduled
    db_meeting.status = MeetingStatus.SCHEDULED

    # Collect emails
    participant_emails = []
    for participant in db_meeting.participants:
        if participant.user and participant.user.email:
            participant_emails.append(participant.user.email)
        elif participant.email:
            participant_emails.append(participant.email)
    participant_emails = list(set(participant_emails))

    # Fetch Agenda for Meeting Pack
    from app.services.pdf_service import pdf_service
    from app.models.models import Agenda, Document, Minutes
    from sqlalchemy import desc, and_
    
    agenda_query = select(Agenda).where(Agenda.meeting_id == meeting_id)
    agenda_result = await db.execute(agenda_query)
    agenda = agenda_result.scalar_one_or_none()
    
    attachments = []
    
    # 1. Attach Agenda (PDF)
    if agenda and agenda.content:
        try:
            # Safeguard TWG/Pillar
            pillar_val = "TWG"
            if db_meeting.twg and db_meeting.twg.pillar:
                pillar_val = db_meeting.twg.pillar.value
                
            pdf_bytes = pdf_service.generate_agenda_pdf(
                agenda_markdown=agenda.content,
                template_context={
                    "pillar_name": pillar_val,
                    "meeting_title": db_meeting.title,
                    "meeting_date": db_meeting.scheduled_at.strftime("%Y-%m-%d"),
                    "meeting_time": db_meeting.scheduled_at.strftime("%H:%M UTC"),
                    "location": db_meeting.location or "Virtual"
                }
            )
            attachments.append({
                "filename": f"Agenda - {db_meeting.title}.pdf",
                "content": pdf_bytes,
                "content_type": "application/pdf"
            })
            print(f"Generated PDF Agenda size: {len(pdf_bytes)} bytes")
        except Exception as e:
            print(f"Failed to generate PDF Agenda: {e}")

    # 2. Compile Meeting Pack (Previous Minutes & Concept Notes)
    # ---------------------------------------------------------
    try:
        # A. Find Previous Approved Minutes for this TWG
        # Sort by created_at desc, filter by status=FINAL/APPROVED
        from sqlalchemy import or_
        minutes_query = select(Minutes).join(Meeting).where(
            Meeting.twg_id == db_meeting.twg_id,
            Meeting.id != meeting_id, # Not this meeting
            or_(Minutes.status == MinutesStatus.FINAL, Minutes.status == MinutesStatus.APPROVED)
        ).order_by(desc(Minutes.created_at)).limit(1)
        
        minutes_result = await db.execute(minutes_query)
        prev_minutes = minutes_result.scalar_one_or_none()
        
        if prev_minutes and prev_minutes.content:
             # Generate PDF from content
             try:
                 # Need to fetch the meeting title for the previous minutes
                 # Lazy load might trigger error if not eager loaded, but let's try
                 # We joined Meeting in query so it might be attached if we selected it, 
                 # but we selected Minutes.
                 # Let's just use generic title or try to access relationship
                 
                 # Better: fetch meeting details for context
                 prev_meeting_result = await db.execute(select(Meeting).where(Meeting.id == prev_minutes.meeting_id))
                 prev_meeting_obj = prev_meeting_result.scalar_one_or_none()
                 
                 prev_title = prev_meeting_obj.title if prev_meeting_obj else "Previous Meeting"
                 prev_date = prev_meeting_obj.scheduled_at.strftime("%Y-%m-%d") if (prev_meeting_obj and prev_meeting_obj.scheduled_at) else "Date Unknown"
                 
                 minutes_pdf = pdf_service.generate_minutes_pdf(
                    minutes_markdown=prev_minutes.content,
                    template_context={
                        "pillar_name": db_meeting.twg.pillar.value if db_meeting.twg else "TWG",
                        "meeting_title": prev_title,
                        "meeting_date": prev_date,
                        "location": prev_meeting_obj.location if prev_meeting_obj else "Virtual",
                        "attendees": [] # Simplified for now
                    }
                 )
                 
                 attachments.append({
                     "filename": f"Minutes - {prev_title}.pdf",
                     "content": minutes_pdf,
                     "content_type": "application/pdf"
                 })
                 print(f"Attached Previous Minutes PDF")
             except Exception as e:
                 print(f"Failed to generate previous minutes PDF: {e}")

        # B. Find relevant "Zero Draft" or "Concept Note" from last 30 days
        # This is a heuristic for "Pre-read materials"
        from datetime import datetime as dt_cls, timedelta
        thirty_days_ago = dt_cls.utcnow() - timedelta(days=30)  # Naive UTC to match DB
        
        docs_query = select(Document).where(
            Document.twg_id == db_meeting.twg_id,
            Document.created_at >= thirty_days_ago, # Recent
            (Document.file_name.ilike("%concept note%") | Document.file_name.ilike("%zero draft%"))
        ).limit(3)
        
        docs_result = await db.execute(docs_query)
        concept_notes = docs_result.scalars().all()
        
        for doc in concept_notes:
            try:
                import os
                if doc.file_path and os.path.exists(doc.file_path):
                    with open(doc.file_path, "rb") as f:
                        content = f.read()
                    attachments.append({
                        "filename": doc.file_name,
                        "content": content,
                        "content_type": doc.file_type or "application/pdf"
                    })
                    print(f"Attached Concept Note: {doc.file_name}")
            except Exception as e:
                print(f"Failed to attach concept note {doc.file_name}: {e}")
                
    except Exception as e:
        print(f"Error compiling meeting pack: {e}")
        # Don't fail the whole send just for attachments
    
    # ---------------------------------------------------------

    # Send emails
    try:
        if participant_emails:
            # Safeguard for potentially missing TWG or Pillar
            pillar_name = "TWG"
            if db_meeting.twg and db_meeting.twg.pillar:
                pillar_name = db_meeting.twg.pillar.value
            
            await email_service.send_meeting_invite(
                to_emails=participant_emails,
                subject=f"INVITATION: {db_meeting.title}",
                template_name="meeting_invite.html",
                template_context={
                    "user_name": "Valued Participant",
                    "meeting_title": db_meeting.title,
                    "meeting_date": db_meeting.scheduled_at.strftime("%Y-%m-%d"),
                    "meeting_time": db_meeting.scheduled_at.strftime("%H:%M UTC"),
                    "location": db_meeting.location or "Virtual",
                    "video_link": db_meeting.video_link,
                    "pillar_name": pillar_name,
                    "portal_url": f"{settings.FRONTEND_URL}/schedule"
                },
                meeting_details={
                    "title": db_meeting.title,
                    "start_time": db_meeting.scheduled_at,
                    "duration": db_meeting.duration_minutes,
                    "location": db_meeting.location
                },
                attachments=attachments
            )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"CRITICAL ERROR: Failed to send invitations for meeting {meeting_id}:\n{error_trace}")
        
        # Return partial success/warning instead of 500 crash
        # This allows the UI to show the specific error message
        return {
            "status": "warning",
            "message": f"Invites failed to send: {str(e)}",
            "emails_sent": 0
        }

    
    # Log Audit
    await audit_service.log_activity(
        db=db,
        user_id=current_user.id,
        action="MEETING_INVITES_SENT",
        resource_type="meeting",
        resource_id=meeting_id,
        details={
            "participant_count": len(participant_emails),
            "pdf_attached": bool(agenda and agenda.content),
            "invite_mode": "email"
        },
        ip_address=request.client.host if request.client else None
    )

    await db.commit()
    return {
        "status": "invites_sent",
        "message": f"Successfully sent invitations to {len(participant_emails)} participant(s).",
        "emails_sent": len(participant_emails)
    }


@router.post("/{meeting_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_meeting(
    meeting_id: uuid.UUID,
    cancel_data: MeetingCancel,
    request: Request,
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

    await audit_service.log_activity(
        db=db,
        user_id=current_user.id,
        action="MEETING_CANCELLED",
        resource_type="meeting",
        resource_id=meeting_id,
        details={
            "reason": cancel_data.reason,
            "notify_participants": cancel_data.notify_participants,
            "emails_sent": emails_sent
        },
        ip_address=request.client.host if request.client else None
    )

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
    
    # 1. Identify emails that need lookup (no user_id provided)
    emails_to_lookup = [
        p.email.lower() for p in participants 
        if not p.user_id and p.email
    ]
    
    # 2. Batch query users
    email_to_userid_map = {}
    if emails_to_lookup:
        res = await db.execute(select(User).where(User.email.in_(emails_to_lookup)))
        found_users = res.scalars().all()
        for u in found_users:
            email_to_userid_map[u.email.lower()] = u.id

    # 3. Check for EXISTING participants to avoid duplicates
    existing_query = select(MeetingParticipant).where(MeetingParticipant.meeting_id == meeting_id)
    existing_res = await db.execute(existing_query)
    existing_participants = existing_res.scalars().all()
    
    existing_user_ids = {p.user_id for p in existing_participants if p.user_id}
    existing_emails = {p.email.lower() for p in existing_participants if p.email}

    for p_in in participants:
         # Determine User ID: Provided > Looked Up > None
         final_user_id = p_in.user_id
         if not final_user_id and p_in.email:
             final_user_id = email_to_userid_map.get(p_in.email.lower())

         # Check Duplicates
         if final_user_id and final_user_id in existing_user_ids:
             continue # Skip
         if p_in.email and p_in.email.lower() in existing_emails:
             continue # Skip

         db_p = MeetingParticipant(
             meeting_id=meeting_id,
             user_id=final_user_id,
             email=p_in.email,
             name=p_in.name,
             rsvp_status=RsvpStatus.PENDING
         )
         db.add(db_p)
         new_participants.append(db_p)
         
    await db.commit()
    
    # Sync to Google Calendar
    try:
        from app.services.calendar_service import calendar_service
        # Get DB meeting to check type
        if db_meeting.meeting_type == 'virtual' or db_meeting.meeting_type == 'hybrid': # Assume virtual/hybrid have links
             emails_to_add = [p.email for p in new_participants if p.email]
             if emails_to_add:
                 calendar_service.add_attendees_to_event(str(meeting_id), emails_to_add)
    except Exception as e:
        # Don't fail the request if sync fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to sync participants to GCal: {e}")
    
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

    generated_content = await agent.chat(prompt)
    
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
    
    # RAG: Retrieve context from Summit Knowledge Repository
    from app.core.knowledge_base import get_knowledge_base
    kb = get_knowledge_base()
    search_query = f"{db_meeting.title} {agenda_content[:100]}"
    try:
        # Search global namespace for general policy (Vision 2050 etc)
        rag_results = kb.search(query=search_query, namespace="global", top_k=3)
        
        # Also search TWG namespace for continuity
        if db_meeting.twg_id:
             twg_results = kb.search(query=search_query, namespace=f"twg-{db_meeting.twg_id}", top_k=2)
             rag_results.extend(twg_results)
             
        rag_context = "\n".join([f"- {r['metadata'].get('file_name', 'Doc')}: {r['text'][:300]}..." for r in rag_results])
    except Exception as e:
        print(f"RAG Retrieval failed: {e}")
        rag_context = "No specific policy context available."

    prompt = f"""Act as the Summit Secretariat Supervisor. Instruct the {pillar_name} TWG Agent to draft professional meeting minutes for the following session.

Meeting Details:
- Title: {db_meeting.title}
- Date: {db_meeting.scheduled_at.strftime('%Y-%m-%d %H:%M UTC') if db_meeting.scheduled_at else 'TBD'}
- Duration: {db_meeting.duration_minutes} minutes
- Location: {db_meeting.location or 'Virtual'}
- TWG Pillar: {pillar_name}

Reference Context (Knowledge Repository):
{rag_context}

Context (Agenda/Transcript):
{agenda_content}

{f"Transcript/Notes:{chr(10)}{context}" if context else "No transcript available. WARNING: Cannot generate minutes without a source record."}

INSTRUCTIONS:
1. **Strict Adherence**: You are a Court Stenographer, not an author. Rely EXCLUSIVELY on the provided Transcript/Notes. Do NOT hallucinate, simulate, or invent details.
2. **Policy Verification**: Cross-reference facts against the Reference Context. 
   - If a claim matches the Reference, cite it (e.g., "Aligned with Vision 2050").
   - If the Reference Context is empty or the claim cannot be verified, DO NOT invent a verification. 
3. **Gap Flagging**: If the transcript is unclear or context is missing for a section, explicitly mark it as `[DRAFT - REQUIRES HUMAN INPUT]`.
4. **Playbook Structure**: Follow the format below exactly.
5. **Output Format**: PURE MARKDOWN only.

STRUCTURE:

# ECOWAS Technical Working Group Meeting Minutes

## Meeting Details
- **Title:** {db_meeting.title}
- **Date:** {db_meeting.scheduled_at.strftime('%Y-%m-%d') if db_meeting.scheduled_at else 'TBD'}
- **Location:** {db_meeting.location or 'Virtual'}
- **Pillar:** {pillar_name}

## Pillar Alignment
[Analyze alignment with Vision 2050 using Reference Context. IF Reference Context is empty, state: "Reference documents unavailable for alignment verification."]

## Executive Summary & Discussion
[Comprehensive summary based ONLY on the transcript. Do not embellish.]

## Decisions Made
[Clearly highlighted points of consensus]
1. ...
2. ...

## Action Items
| Owner | Task | Due Date |
|-------|------|----------|
| [Name/Title] | [Specific Task] | [Date or TBD] |

## Next Steps
[Brief summary of immediate next steps]

## Closing
[Closing remarks]"""

    generated_content = agent.chat(prompt)
    
    # Persist headers
    result_min = await db.execute(select(Minutes).where(Minutes.meeting_id == meeting_id))
    existing_minutes = result_min.scalar_one_or_none()
    
    if existing_minutes:
        existing_minutes.content = generated_content
        existing_minutes.status = MinutesStatus.DRAFT
    else:
        new_minutes = Minutes(
            meeting_id=meeting_id,
            content=generated_content,
            status=MinutesStatus.DRAFT
        )
        db.add(new_minutes)
    
    await db.commit()
    
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
    print(f"DEBUG: submit_minutes called for {meeting_id}")
    # Get meeting and minutes
    try:
        result = await db.execute(
            select(Meeting)
            .options(
                selectinload(Meeting.minutes),
                selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
                selectinload(Meeting.twg)
            )
            .where(Meeting.id == meeting_id)
        )
    except Exception as e:
        import traceback
        print(f"DEBUG: DB Load Failed: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"DB Load Failed: {e}")
        
    print(f"DEBUG: submit_minutes query executed")
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not db_meeting.minutes:
        raise HTTPException(status_code=400, detail="No minutes to submit")
    
    if db_meeting.minutes.status not in [MinutesStatus.DRAFT, MinutesStatus.REVIEW]:
        raise HTTPException(
            status_code=400, 
            detail=f"Minutes must be in DRAFT or REVIEW status to submit. Current: {db_meeting.minutes.status.value}"
        )
    
    # Update status
    db_meeting.minutes.status = MinutesStatus.PENDING_APPROVAL
    
    # Clear rejection info on resubmission
    if db_meeting.minutes.rejection_reason:
        db_meeting.minutes.rejected_at = None
        db_meeting.minutes.rejection_reason = None
        
    try:
        await db.commit()
        await db.refresh(db_meeting.minutes)
    except Exception as e:
        import traceback
        logger.error(f"DB Commit Failed during minutes submission: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Database error during submission: {str(e)}")

    # --- Notification Logic ---

    try:
        from app.models.models import Notification, NotificationType
        
        # Notify ALL Admins and Secretariat Leads
        result = await db.execute(select(User).where(User.role.in_([UserRole.ADMIN, UserRole.SECRETARIAT_LEAD])))
        reviewers = result.scalars().all()
        
        # If no high-level reviewers, fallback to TWG Technical Lead
        if not reviewers:
            if db_meeting.twg and db_meeting.twg.technical_lead_id:
                reviewer = await db.execute(select(User).where(User.id == db_meeting.twg.technical_lead_id))
                user = reviewer.scalar_one_or_none()
                if user:
                    reviewers.append(user)

        # Create notifications
        if reviewers:
            for reviewer in reviewers:
                notification = Notification(
                    user_id=reviewer.id,
                    type=NotificationType.TASK,
                    title="Minutes Approval Required",
                    content=f"Minutes for '{db_meeting.title}' submitted by {current_user.full_name}. Please review and approve.",
                    link=f"/meetings/{meeting_id}"
                )
                db.add(notification)
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to send approval notifications: {e}")
        # Non-blocking, proceed

    
    return {
        "message": "Minutes submitted for approval",
        "status": db_meeting.minutes.status.value,
        "meeting_id": str(meeting_id),
        "approved_by": current_user.full_name
    }


@router.post("/{meeting_id}/minutes/approve")
async def approve_minutes(
    meeting_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve minutes. Changes status from PENDING_APPROVAL to APPROVED.
    Triggers: PDF Generation, Email Distribution, KB Indexing, Audit Logging.
    """
    # Get meeting and minutes
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.minutes),
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
        
    # Enforce Secretariat Lead (or Admin) approval
    if current_user.role not in [UserRole.SECRETARIAT_LEAD, UserRole.ADMIN]:
        raise HTTPException(
            status_code=403, 
            detail="Only Secretariat Leads can approve minutes. Please submit for approval instead."
        )
    
    if not db_meeting.minutes:
        raise HTTPException(status_code=400, detail="No minutes to approve")
    
    if db_meeting.minutes.status != MinutesStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail=f"Minutes must be PENDING_APPROVAL to approve. Current: {db_meeting.minutes.status.value}")
    
    # Approve
    db_meeting.minutes.status = MinutesStatus.APPROVED
    await db.commit()
    await db.refresh(db_meeting.minutes)
    
    # --- Post-Approval Workflows ---
    
    # 1. Generate Official PDF
    pdf_bytes = None
    try:
        from app.services.pdf_service import pdf_service
        
        pillar_display = db_meeting.twg.pillar.value.replace("_", " ").title() if db_meeting.twg else "General"
        pdf_context = {
            "pillar_name": pillar_display,
            "meeting_title": db_meeting.title,
            "meeting_date": db_meeting.scheduled_at.strftime('%Y-%m-%d') if db_meeting.scheduled_at else "TBD",
            "meeting_time": db_meeting.scheduled_at.strftime('%H:%M') if db_meeting.scheduled_at else "",
            "location": db_meeting.location or "Virtual",
        }
        pdf_bytes = pdf_service.generate_minutes_pdf(
            minutes_markdown=db_meeting.minutes.content,
            template_context=pdf_context
        )
    except Exception as e:
        print(f"PDF Gen Failure: {e}")
        # Log warning but don't crash, the status is already updated
    
    # 2. Index to Knowledge Base (RAG)
    try:
        from app.core.knowledge_base import get_knowledge_base
        kb = get_knowledge_base()
        kb.add_document(
            content=db_meeting.minutes.content,
            metadata={
                "source": "official_minutes",
                "meeting_id": str(db_meeting.id),
                "date": db_meeting.scheduled_at.isoformat() if db_meeting.scheduled_at else None,
                "pillar": db_meeting.twg.pillar.value if db_meeting.twg else "unknown",
                "status": "approved",
                "file_name": f"Minutes - {db_meeting.title}"
            },
            namespace=f"twg-{db_meeting.twg_id}" if db_meeting.twg_id else "global"
        )
    except Exception as e:
        print(f"KB Indexing Failed: {e}")

    # 3. Send Emails to Participants
    recipients = set()
    
    for p in db_meeting.participants:
        # 1. Registered User Email
        if p.user and p.user.email:
            recipients.add(p.user.email)
        # 2. Guest Email (stored directly on participant record)
        elif p.email:
            recipients.add(p.email)
            
    recipient_list = list(recipients)
    
    if pdf_bytes and recipient_list:
        try:
             email_context = {
                 "recipient_name": "Colleague", 
                 "meeting_title": db_meeting.title,
                 "date_str": db_meeting.scheduled_at.strftime('%Y-%m-%d') if db_meeting.scheduled_at else "TBD",
                 "pillar_name": pillar_display,
                 "dashboard_url": f"{settings.FRONTEND_URL}/meetings/{db_meeting.id}"
             }
             await email_service.send_minutes_published_email(
                 to_emails=recipient_list,
                 template_context=email_context,
                 pdf_content=pdf_bytes,
                 pdf_filename="minutes.pdf"
             )
        except Exception as e:
            print(f"Email Sending Failed: {e}")
            # Non-blocking

    # --- Audit Log ---
    from app.services.audit_service import audit_service
    
    await audit_service.log_activity(
        db,
        user_id=current_user.id,
        action="MEETING_MINUTES_APPROVED",
        resource_type="meeting",
        resource_id=meeting_id,
        details={
            "meeting_title": db_meeting.title,
            "actions": "generated_pdf, sent_email, indexed_kb",
            "recipients": recipient_list  # Explicitly log who got it
        },
        ip_address=request.client.host if request.client else None
    )
    
    return {
        "message": "Minutes approved and published",
        "status": db_meeting.minutes.status.value,
        "workflows_triggered": ["pdf", "email", "audit", "kb_indexing"] 
    }


@router.get("/{meeting_id}/minutes/pdf")
async def download_minutes_pdf(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download meeting minutes as PDF.
    Available for APPROVED or FINAL status only.
    """
    from fastapi.responses import Response
    from app.services.pdf_service import pdf_service
    
    # Get meeting with minutes and TWG
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.minutes), selectinload(Meeting.twg))
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not db_meeting.minutes:
        raise HTTPException(status_code=404, detail="No minutes found for this meeting")
    
    # Allow download for APPROVED and FINAL status (also DRAFT for preview)
    allowed_statuses = [MinutesStatus.APPROVED, MinutesStatus.FINAL, MinutesStatus.DRAFT, MinutesStatus.PENDING_APPROVAL]
    if db_meeting.minutes.status not in allowed_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Minutes must be in APPROVED, FINAL, DRAFT, or PENDING_APPROVAL status. Current: {db_meeting.minutes.status.value}"
        )
    
    # Generate PDF
    pillar_display = db_meeting.twg.pillar.value.replace("_", " ").title() if db_meeting.twg else "General"
    pdf_context = {
        "pillar_name": pillar_display,
        "meeting_title": db_meeting.title,
        "meeting_date": db_meeting.scheduled_at.strftime('%Y-%m-%d') if db_meeting.scheduled_at else "TBD",
        "meeting_time": db_meeting.scheduled_at.strftime('%H:%M') if db_meeting.scheduled_at else "",
        "location": db_meeting.location or "Virtual",
    }
    
    try:
        pdf_bytes = pdf_service.generate_minutes_pdf(
            minutes_markdown=db_meeting.minutes.content,
            template_context=pdf_context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
    
    # Create safe filename
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in db_meeting.title)[:50]
    filename = f"Minutes_{safe_title}.pdf"
    
    # Add watermark for non-approved minutes
    status_label = ""
    if db_meeting.minutes.status == MinutesStatus.DRAFT:
        status_label = "DRAFT_"
    elif db_meeting.minutes.status == MinutesStatus.PENDING_APPROVAL:
        status_label = "PENDING_"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={status_label}{filename}"
        }
    )


@router.post("/{meeting_id}/minutes/reject")
async def reject_minutes(
    meeting_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_facilitator),
    db: AsyncSession = Depends(get_db)
):
    """
    Reject minutes and send back for revision.
    Changes status from PENDING_APPROVAL to REVIEW.
    Stores rejection reason and notifies the TWG lead.
    """
    from datetime import datetime
    from app.models.models import Notification, NotificationType
    
    # Parse body
    body = await request.json()
    rejection_reason = body.get("reason", "No reason provided")
    suggested_changes = body.get("suggested_changes", "")
    
    # Get meeting and minutes
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.minutes),
            selectinload(Meeting.twg).selectinload(TWG.technical_lead)
        )
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result.scalar_one_or_none()
    
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not has_twg_access(current_user, db_meeting.twg_id):
        raise HTTPException(status_code=403, detail="Access denied")
        
    # Enforce Secretariat Lead (or Admin) rejection
    if current_user.role not in [UserRole.SECRETARIAT_LEAD, UserRole.ADMIN]:
        raise HTTPException(
            status_code=403, 
            detail="Only Secretariat Leads can reject minutes. Please contact support if you need to revert status."
        )
    
    if not db_meeting.minutes:
        raise HTTPException(status_code=400, detail="No minutes to reject")
    
    if db_meeting.minutes.status != MinutesStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=400, 
            detail=f"Minutes must be PENDING_APPROVAL to reject. Current: {db_meeting.minutes.status.value}"
        )
    
    # Update status to REVIEW
    db_meeting.minutes.status = MinutesStatus.REVIEW
    
    # Store rejection reason in key_decisions field (or add metadata)
    # We'll prepend a rejection note to the key_decisions field
    rejection_note = f"[REJECTION - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}]\nReason: {rejection_reason}"
    if suggested_changes:
        rejection_note += f"\nSuggested Changes: {suggested_changes}"
    rejection_note += "\n---\n"
    
    if db_meeting.minutes.key_decisions:
        db_meeting.minutes.key_decisions = rejection_note + db_meeting.minutes.key_decisions
    else:
        db_meeting.minutes.key_decisions = rejection_note
    
    await db.commit()
    await db.refresh(db_meeting.minutes)
    
    # Create notification for TWG lead
    if db_meeting.twg and db_meeting.twg.technical_lead:
        notification = Notification(
            user_id=db_meeting.twg.technical_lead.id,
            type=NotificationType.ALERT,
            title="Minutes Rejected",
            content=f"Minutes for '{db_meeting.title}' were rejected. Reason: {rejection_reason}",
            link=f"/meetings/{meeting_id}"
        )
        db.add(notification)
        await db.commit()
    
    # Audit log
    await audit_service.log_activity(
        db=db,
        user_id=current_user.id,
        action="MEETING_MINUTES_REJECTED",
        resource_type="meeting",
        resource_id=meeting_id,
        details={
            "meeting_title": db_meeting.title,
            "reason": rejection_reason,
            "suggested_changes": suggested_changes
        },
        ip_address=request.client.host if request.client else None
    )
    
    return {
        "message": "Minutes rejected and sent back for revision",
        "status": db_meeting.minutes.status.value,
        "reason": rejection_reason
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
    agent_map = {
        "energy_infrastructure": "energy",
        "agriculture_food_systems": "agriculture",
        "critical_minerals_industrialization": "minerals",
        "digital_economy_transformation": "digital",
        "protocol_logistics": "protocol",
        "resource_mobilization": "resource_mobilization"
    }
    agent_id = agent_map.get(pillar, "energy")
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
    # Deduplication: Fetch existing actions first
    try:
        existing_result = await db.execute(select(ActionItem).where(ActionItem.meeting_id == meeting_id))
        existing_actions = existing_result.scalars().all()
        existing_descriptions = {a.description.strip().lower() for a in existing_actions}
    except Exception as e:
        print(f"DEDUPE ERROR: {e}")
        # Fallback to empty to allow proceed
        existing_descriptions = set()

    created_items = []
    for item in extracted_items:
        # Check duplicate
        desc = item.get("description", "").strip()
        if not desc or desc.lower() in existing_descriptions:
            continue

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
    try:
        os.makedirs(upload_dir, exist_ok=True)
        
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_size = os.path.getsize(file_path)
    except Exception as e:
        import traceback
        print(f"File Upload Error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    db_document = Document(
        twg_id=db_meeting.twg_id,
        meeting_id=meeting_id, # Link to meeting!
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
