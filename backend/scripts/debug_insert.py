import asyncio
import uuid
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.models.models import Project, ProjectStatus, TWG, TWGPillar

async def try_insert():
    async with AsyncSessionLocal() as session:
        # Create Dummy TWG
        twg = TWG(name="Debug TWG", pillar=TWGPillar.energy_infrastructure)
        session.add(twg)
        await session.commit()
        await session.refresh(twg)
        
        # Create Project
        p = Project(
            twg_id=twg.id,
            name="Debug Project",
            description="Test",
            investment_size=100,
            readiness_score=5,
            status=ProjectStatus.DRAFT # "draft"
        )
        session.add(p)
        try:
            await session.commit()
            print("Successfully inserted project with status DRAFT")
        except Exception as e:
            print(f"Insertion failed: {e}")

if __name__ == "__main__":
    asyncio.run(try_insert())
