
import asyncio
import uuid
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.models import Meeting, Minutes, TWG, User, UserRole, TWGPillar, MeetingStatus, MinutesStatus

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async def test_minutes_creation():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        try:
            print("Creating User...")
            user = User(id=uuid.uuid4(), full_name="Test", email="test@test.com", hashed_password="pw", role=UserRole.TWG_FACILITATOR)
            session.add(user)
            
            print("Creating TWG...")
            twg = TWG(id=uuid.uuid4(), name="Test TWG", pillar=TWGPillar.energy_infrastructure)
            session.add(twg)
            await session.commit()
            
            print("Creating Meeting...")
            meeting_id = uuid.uuid4()
            meeting = Meeting(
                id=meeting_id,
                twg_id=twg.id,
                title="Test Meeting",
                scheduled_at=os.path.getmtime(__file__) # just a timestamp
            )
            # Fix scheduled_at
            from datetime import datetime
            meeting.scheduled_at = datetime.utcnow()
            session.add(meeting)
            await session.commit()
            print(f"Meeting created with ID: {meeting.id}")
            
            print("Creating Minutes...")
            minutes = Minutes(
                meeting_id=meeting.id,
                content="Test Content",
                status=MinutesStatus.FINAL
            )
            session.add(minutes)
            await session.commit()
            print("Minutes created successfully!")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_minutes_creation())
