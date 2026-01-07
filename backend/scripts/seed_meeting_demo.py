import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend directory to path
# Add backend directory and project root to path
sys.path.append(str(Path(__file__).parent.parent)) # backend/
sys.path.append(str(Path(__file__).parent.parent.parent)) # project root/

from app.core.database import AsyncSessionLocal
from app.models.models import TWG, Meeting, MeetingStatus, RsvpStatus, MeetingParticipant
from sqlalchemy import select

async def seed_meetings():
    print("🌱 Seeding Demo Meetings...")
    async with AsyncSessionLocal() as db:
        try:
            # Get a TWG
            result = await db.execute(select(TWG).limit(1))
            twg = result.scalar_one_or_none()
            
            if not twg:
                print("❌ No TWG found. Please run sync_twgs.py first.")
                return

            print(f"Assigning meetings to TWG: {twg.name}")

            # 1. Upcoming TWG Meeting
            m1 = Meeting(
                title="Energy Grid Integration Workshop",
                twg_id=twg.id,
                scheduled_at=datetime.utcnow() + timedelta(days=2),
                duration_minutes=90,
                location="Conference Room A",
                status=MeetingStatus.SCHEDULED
            )
            db.add(m1)
            
            # 2. Past Meeting
            m2 = Meeting(
                title="Q1 Planning Session",
                twg_id=twg.id,
                scheduled_at=datetime.utcnow() - timedelta(days=7),
                duration_minutes=60,
                location="Virtual (Zoom)",
                status=MeetingStatus.COMPLETED
            )
            db.add(m2)

            # 3. Plenary
            m3 = Meeting(
                title="Summit Opening Plenary",
                twg_id=twg.id, # Technically plenary might not have TWG, but schema requires it currently or nullable? Let's check model. 
                # Model has twg_id as ForeignKey. If nullable, great. If not, assign to this TWG for now.
                scheduled_at=datetime.utcnow() + timedelta(days=1, hours=4),
                duration_minutes=120,
                location="Main Hall",
                status=MeetingStatus.SCHEDULED
            )
            db.add(m3)

            await db.commit()
            print("✅ Added 3 meetings.")

        except Exception as e:
            print(f"❌ Error seeding meetings: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(seed_meetings())
