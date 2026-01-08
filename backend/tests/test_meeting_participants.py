
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.api.routes.meetings import add_participants, schedule_meeting_trigger
from app.models.models import Meeting, User, MeetingParticipant, TWG, RsvpStatus
from app.schemas.schemas import MeetingParticipantCreate

@pytest.mark.asyncio
async def test_add_participants_logic():
    # Setup Mocks
    mock_db = AsyncMock()
    mock_user = MagicMock(spec=User)
    mock_user.id = uuid4()
    
    meeting_id = uuid4()
    twg_id = uuid4()
    
    # Mock Meeting exists
    mock_meeting = MagicMock(spec=Meeting)
    mock_meeting.id = meeting_id
    mock_meeting.twg_id = twg_id
    
    # Mock DB execute result for Meeting check
    mock_result_meeting = MagicMock()
    mock_result_meeting.scalar_one_or_none.return_value = mock_meeting
    
    mock_db.execute.return_value = mock_result_meeting

    # Mock Access Rights
    with patch("app.api.routes.meetings.has_twg_access", return_value=True):
        
        # Test Data
        participants_in = [
            MeetingParticipantCreate(name="External Guest", email="guest@example.com"),
            MeetingParticipantCreate(user_id=uuid4())
        ]
        
        # Call Function
        result = await add_participants(
            meeting_id=meeting_id,
            participants=participants_in,
            current_user=mock_user,
            db=mock_db
        )
        
        # Verify
        assert len(result) == 2
        assert mock_db.add.call_count == 2
        assert mock_db.commit.called
        
        # Check that MeetingParticipant objects were created correctly
        # First one (Guest)
        call_args_1 = mock_db.add.call_args_list[0][0][0]
        assert isinstance(call_args_1, MeetingParticipant)
        assert call_args_1.email == "guest@example.com"
        assert call_args_1.user_id is None
        
        # Second one (User)
        call_args_2 = mock_db.add.call_args_list[1][0][0]
        assert isinstance(call_args_2, MeetingParticipant)
        assert call_args_2.user_id == participants_in[1].user_id
        assert call_args_2.email is None


@pytest.mark.asyncio
async def test_schedule_meeting_trigger_email_logic():
    # Setup Mocks
    mock_db = AsyncMock()
    mock_user = MagicMock(spec=User)
    
    meeting_id = uuid4()
    
    # Mock Meeting with Participants
    mock_meeting = MagicMock(spec=Meeting)
    mock_meeting.id = meeting_id
    mock_meeting.title = "Test Meeting"
    mock_meeting.scheduled_at = datetime.utcnow()
    mock_meeting.duration_minutes = 60
    mock_meeting.location = "Virtual"
    mock_meeting.twg = MagicMock(spec=TWG)
    mock_meeting.twg.pillar.value = "Infrastructure"
    
    # Participant 1: Registered User
    p1 = MagicMock(spec=MeetingParticipant)
    p1.user = MagicMock(spec=User)
    p1.user.email = "user@example.com"
    p1.email = None # Should not be used if user is present
    
    # Participant 2: External Guest
    p2 = MagicMock(spec=MeetingParticipant)
    p2.user = None
    p2.email = "guest@example.com"
    
    mock_meeting.participants = [p1, p2]
    
    # Mock DB Query Result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_meeting
    mock_db.execute.return_value = mock_result
    
    # Mock Access Rights
    with patch("app.api.routes.meetings.has_twg_access", return_value=True), \
         patch("app.api.routes.meetings.email_service.send_meeting_invite", new_callable=AsyncMock) as mock_send_email:
        
        # Call Function
        result = await schedule_meeting_trigger(
            meeting_id=meeting_id,
            current_user=mock_user,
            db=mock_db
        )
        
        # Verify
        assert result["status"] == "successfully scheduled"
        assert result["emails_sent"] == 2 # Should find both
        
        # Check that send_meeting_invite was called with correct emails
        assert mock_send_email.called
        call_kwargs = mock_send_email.call_args.kwargs
        to_emails = call_kwargs["to_emails"]
        
        assert "user@example.com" in to_emails
        assert "guest@example.com" in to_emails
