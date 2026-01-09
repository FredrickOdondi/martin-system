
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.core.database import Base
from app.models.models import Meeting, User, MeetingStatus, TWG, TWGPillar, UserRole, MeetingParticipant
from app.api.routes.meetings import schedule_meeting_trigger
from app.core.config import settings

# SQLite in-memory database for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_schedule_uses_frontend_url(db_session):
    # PREPARE DATA
    user = User(
        id=uuid4(), 
        full_name="Test Facilitator", 
        email="test@example.com", 
        hashed_password="hash",
        role=UserRole.TWG_FACILITATOR
    )
    db_session.add(user)
    
    twg = TWG(
        id=uuid4(),
        name="Test TWG",
        pillar=TWGPillar.energy_infrastructure
    )
    db_session.add(twg)
    await db_session.commit()
    
    meeting = Meeting(
        id=uuid4(),
        twg_id=twg.id,
        title="URL Test Meeting",
        scheduled_at=datetime.now(timezone.utc),
        duration_minutes=60,
        status=MeetingStatus.SCHEDULED
    )
    db_session.add(meeting)
    await db_session.commit()
    
    participant = MeetingParticipant(
        meeting_id=meeting.id,
        user_id=user.id
    )
    db_session.add(participant)
    await db_session.commit()

    # MOCK & ACT
    # Patch the email service method used in the route
    with patch("app.services.email_service.email_service.send_meeting_invite", new_callable=AsyncMock) as mock_send:
        # Also patch access control
        with patch("app.api.routes.meetings.has_twg_access", return_value=True):
            
            # Temporarily force FRONTEND_URL to a known test value to be sure
            original_url = settings.FRONTEND_URL
            test_url = "https://unit-test-frontend.com"
            settings.FRONTEND_URL = test_url
            
            try:
                await schedule_meeting_trigger(
                    meeting_id=meeting.id,
                    current_user=user,
                    db=db_session
                )
                
                # ASSERT
                assert mock_send.called
                call_args = mock_send.call_args[1] # kwargs
                template_context = call_args["template_context"]
                
                print(f"Captured portal_url: {template_context['portal_url']}")
                assert template_context["portal_url"] == f"{test_url}/schedule"
                
            finally:
                settings.FRONTEND_URL = original_url
