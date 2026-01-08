
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.api.routes.meetings import create_meeting
from app.models.models import Meeting, User, MeetingStatus
from app.schemas.schemas import MeetingCreate

@pytest.mark.asyncio
async def test_create_meeting_repro():
    """Attempt to reproduce 500 error on meeting creation"""
    
    # Setup Mocks
    mock_db = AsyncMock()
    mock_user = MagicMock(spec=User)
    mock_user.id = uuid4()
    
    # Test Data
    meeting_data = MeetingCreate(
        twg_id=uuid4(),
        title="Test Meeting",
        scheduled_at=datetime.utcnow(),
        duration_minutes=60,
        location="Virtual"
    )
    
    # Mock Access Rights
    with patch("app.api.routes.meetings.has_twg_access", return_value=True):
        
        try:
            # Call Function
            result = await create_meeting(
                meeting_in=meeting_data,
                current_user=mock_user,
                db=mock_db
            )
            print("Successfully created meeting")
        except Exception as e:
            print(f"Caught exception: {e}")
            raise e
