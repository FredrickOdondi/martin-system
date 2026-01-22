
import asyncio
import sys
import os
from sqlalchemy import select, delete

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.models import TWG, Meeting, Document, Project, Conflict
from app.core.database import get_db_session_context

async def cleanup_test_data():
    print("Starting cleanup of test data with explicit cascade...")
    
    async with get_db_session_context() as session:
        # 1. Find Test TWGs
        result = await session.execute(
            select(TWG).where(TWG.name.like("Test TWG%"))
        )
        test_twgs = result.scalars().all()
        test_twg_ids = [twg.id for twg in test_twgs]
        
        if not test_twgs:
            print("No 'Test TWG' records found.")
        else:
            print(f"Found {len(test_twgs)} Test TWGs. Cleaning dependencies...")
            
            # Delete Meetings
            print(f"Deleting meetings for {len(test_twgs)} TWGs...")
            # We fetch first to log, or just delete directly
            await session.execute(
                delete(Meeting).where(Meeting.twg_id.in_(test_twg_ids))
            )
            
            # Delete Documents
            print(f"Deleting documents for {len(test_twgs)} TWGs...")
            await session.execute(
                delete(Document).where(Document.twg_id.in_(test_twg_ids))
            )
            
            # Delete Projects
            print(f"Deleting projects for {len(test_twgs)} TWGs...")
            await session.execute(
                delete(Project).where(Project.twg_id.in_(test_twg_ids))
            )
            
            # Now delete the TWGs
            print(f"Deleting {len(test_twgs)} TWGs...")
            await session.execute(
                 delete(TWG).where(TWG.id.in_(test_twg_ids))
            )
            
        # 2. Find Test Conflicts
        result_conflicts = await session.execute(
            select(Conflict).where(Conflict.description.like("%Test Conflict%"))
        )
        test_conflicts = result_conflicts.scalars().all()
        test_conflict_ids = [c.id for c in test_conflicts]
        
        if not test_conflicts:
            print("No 'Test Conflict' records found.")
        else:
            print(f"Found {len(test_conflicts)} Test Conflicts. Deleting...")
            await session.execute(
                delete(Conflict).where(Conflict.id.in_(test_conflict_ids))
            )

        await session.commit()
        print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(cleanup_test_data())
