
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.models import Conflict, ConflictType, ConflictSeverity, ConflictStatus
import uuid
import datetime

async def seed_conflicts():
    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        conflicts = [
            Conflict(
                id=uuid.uuid4(),
                conflict_type=ConflictType.RESOURCE_CONSTRAINT,
                severity=ConflictSeverity.HIGH,
                description="Budget conflict in budget allocation between Energy and Infrastructure",
                agents_involved=["Energy Agent", "Infrastructure Agent"],
                conflicting_positions={
                    "Energy Agent": "Requesting $50M for Solar Grid",
                    "Infrastructure Agent": "Allocating only $30M for Grid updates"
                },
                status=ConflictStatus.DETECTED,
                detected_at=datetime.datetime.utcnow()
            ),
            Conflict(
                id=uuid.uuid4(),
                conflict_type=ConflictType.SCHEDULE_CLASH,
                severity=ConflictSeverity.CRITICAL,
                description="Double booking for Minister of Energy",
                agents_involved=["Energy TWG", "Finance TWG"],
                conflicting_positions={
                    "Energy TWG": "Energy Summit Keynote (10:00 AM)",
                    "Finance TWG": "Budget Review (10:00 AM)"
                },
                status=ConflictStatus.ESCALATED,
                human_action_required=True,
                detected_at=datetime.datetime.utcnow()
            )
        ]
        
        db.add_all(conflicts)
        await db.commit()
        print("Seeded conflicts successfully!")

if __name__ == "__main__":
    asyncio.run(seed_conflicts())
