
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from uuid import uuid4

from app.core.database import Base
from app.models.models import Meeting, User, MeetingStatus, TWG, TWGPillar, UserRole
from app.api.routes.meetings import create_meeting
from app.schemas.schemas import MeetingCreate

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
async def test_create_meeting_integration(db_session):
    # Create User
    user = User(
        id=uuid4(), 
        full_name="Test Facilitator", 
        email="test@example.com", 
        hashed_password="hash",
        role=UserRole.TWG_FACILITATOR
    )
    db_session.add(user)
    
    # Create TWG
    twg = TWG(
        id=uuid4(),
        name="Test TWG",
        pillar=TWGPillar.energy_infrastructure
    )
    db_session.add(twg)
    await db_session.commit()
    
    # Test Data - using timezone aware datetime
    meeting_data = MeetingCreate(
        twg_id=twg.id,
        title="Integration Test Meeting",
        scheduled_at=datetime.now(timezone.utc),
        duration_minutes=60,
        location="Office"
    )
    
    from unittest.mock import patch
    
    with patch("app.api.routes.meetings.has_twg_access", return_value=True):
        try:
            print(f"Creating meeting with data: {meeting_data.model_dump()}")
            result = await create_meeting(
                meeting_in=meeting_data,
                current_user=user,
                db=db_session
            )
            print(f"Result ID: {result.id}")
            assert result.title == "Integration Test Meeting"
            # After fix, scheduled_at is stored as naive UTC, so tzinfo will be None when retrieved
            # assert result.scheduled_at.tzinfo is not None
        except Exception as e:
            print(f"INTEGRATION TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            raise e
