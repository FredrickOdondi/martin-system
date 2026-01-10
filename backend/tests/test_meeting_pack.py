
import pytest
import uuid
import os
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi import Request

from app.core.database import Base
from app.models.models import User, TWG, Meeting, Minutes, Document, MeetingParticipant, MeetingStatus, MinutesStatus, TWGPillar, UserRole
from app.api.routes.meetings import approve_and_send_invite

# Setup in-memory DB
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.mark.asyncio
async def test_meeting_pack_compilation():
    # Setup DB
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as db_session:
        # 1. Setup Data
        user_id = uuid.uuid4()
        twg_id = uuid.uuid4()
        
        # Create User
        user = User(id=user_id, email="lazarusogero1@gmail.com", full_name="Facilitator", role=UserRole.TWG_FACILITATOR)
        db_session.add(user)
        
        # Create TWG
        twg = TWG(id=twg_id, name="Test TWG", pillar=TWGPillar.energy_infrastructure)
        db_session.add(twg)
        user.twgs.append(twg)
        await db_session.commit()
        
        # Create Previous Meeting
        prev_meeting_id = uuid.uuid4()
        prev_meeting = Meeting(
            id=prev_meeting_id, twg_id=twg_id, title="Previous Meeting",
            scheduled_at=datetime.now(timezone.utc) - timedelta(days=10),
            status=MeetingStatus.COMPLETED
        )
        db_session.add(prev_meeting)
        await db_session.commit()
        
        # Create dummy PDF for minutes
        minutes_file = "test_minutes.pdf"
        with open(minutes_file, "w") as f: f.write("dummy pdf content")
        
        # Create Minutes
        minutes = Minutes(
            id=uuid.uuid4(),
            meeting_id=prev_meeting_id, 
            content="Old minutes content", 
            key_decisions="None",
            status=MinutesStatus.FINAL,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(minutes)
        await db_session.commit()
        
        # Create Zero Draft Document
        doc_path = os.path.abspath("zero_draft.pdf")
        with open(doc_path, "w") as f: f.write("dummy doc content")
        
        doc = Document(
            id=uuid.uuid4(),
            twg_id=twg_id,
            file_name="Zero Draft Concept Note.pdf",
            file_path=doc_path,
            file_type="application/pdf",
            uploaded_by_id=user_id,
            is_confidential=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(doc)
        
        # Create Current Meeting
        current_meeting_id = uuid.uuid4()
        current_meeting = Meeting(
            id=current_meeting_id,
            twg_id=twg_id,
            title="Current Meeting",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            status=MeetingStatus.SCHEDULED
        )
        db_session.add(current_meeting)
        
        # Add Participant
        part = MeetingParticipant(
            id=uuid.uuid4(),
            meeting_id=current_meeting_id, 
            user_id=user_id,
            rsvp_status="pending",
            attended=False
        )
        db_session.add(part)
        
        await db_session.commit()
        
        # 2. Mock Dependencies
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        
        # Mock Email Service
        with patch("app.services.email_service.email_service.send_meeting_invite") as mock_send:
            # 3. Call Function
            # IMPORTANT: Pass the SAME session we used to create data
            await approve_and_send_invite(
                meeting_id=current_meeting_id,
                request=mock_request,
                current_user=user,
                db=db_session
            )
            
            # 4. Verify Attachments
            assert mock_send.called
            call_args = mock_send.call_args
            kwargs = call_args.kwargs
            
            # Check receiver email
            to_emails = kwargs.get('to_emails', [])
            assert "lazarusogero1@gmail.com" in to_emails
            
            attachments = kwargs.get('attachments', [])
            filenames = [a['filename'] for a in attachments]
            print(f"Attachments found: {filenames}")
            
            # Should have Minutes and Concept Note
            assert any("Previous Minutes" in f for f in filenames)
            assert "Zero Draft Concept Note.pdf" in filenames

        # Cleanup
        if os.path.exists("test_minutes.pdf"): os.remove("test_minutes.pdf")
        if os.path.exists("zero_draft.pdf"): os.remove("zero_draft.pdf")
    
    await engine.dispose()

