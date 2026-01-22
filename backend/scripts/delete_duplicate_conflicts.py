
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_, func
from app.core.config import settings
from app.models.models import Conflict, ConflictStatus

async def delete_duplicates():
    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        print("Scanning for duplicates...")
        
        # Get all conflicts
        result = await db.execute(select(Conflict).order_by(Conflict.detected_at.desc()))
        conflicts = result.scalars().all()
        
        # Group by unique signature
        # Signature = (type, description, agents_involved_str)
        unique_conflicts = {}
        duplicates_to_delete = []

        for c in conflicts:
            agents_str = ",".join(sorted(c.agents_involved or []))
            sig = (c.conflict_type, c.description, agents_str)
            
            if sig not in unique_conflicts:
                unique_conflicts[sig] = c
            else:
                # If we already have one, check if the current one is "better" to keep?
                # We sorted by detected_at DESC, so the first one we see is the NEWEST.
                # However, maybe we want to keep the OLDEST one to preserve history?
                # OR we keep the one that is NOT DETECTED (i.e. if one is RESOLVED, keep that).
                
                existing = unique_conflicts[sig]
                
                # Preference logic:
                # 1. Prefer non-DETECTED status (Work in progress or Resolved)
                # 2. Prefer Older timestamp? (Stability) OR Newer? (Relevance)
                
                # Let's say we prefer Keeping the one that has been acted upon.
                existing_has_action = existing.status != ConflictStatus.DETECTED
                current_has_action = c.status != ConflictStatus.DETECTED
                
                if current_has_action and not existing_has_action:
                    # Replace existing with current (keep current)
                    duplicates_to_delete.append(existing)
                    unique_conflicts[sig] = c
                elif existing_has_action and not current_has_action:
                    # Keep existing
                    duplicates_to_delete.append(c)
                else:
                    # Both same status class. Keep the NEWEST one (which we saw first in loop),
                    # so delete the current one (which is older because we iterate desc?)
                    # Wait, iterate desc means 1st is Newest.
                    # Dictionary defaults to keeping the first one seen.
                    # So prompt implies "delete duplicate", usually meaning keeping one.
                    # Let's keep the NEWEST active one.
                    duplicates_to_delete.append(c)
        
        print(f"Found {len(duplicates_to_delete)} duplicates to delete out of {len(conflicts)} total.")
        
        if duplicates_to_delete:
            ids = [c.id for c in duplicates_to_delete]
            # Chunk deletion if necessary, but 2000 is fine.
            # Using execute delete with in_ for efficiency
            # await db.execute(delete(Conflict).where(Conflict.id.in_(ids))) # syntax check
            
            # OR delete one by one to use session delete
            for d in duplicates_to_delete:
                await db.delete(d)
                
            await db.commit()
            print(f"Deleted {len(duplicates_to_delete)} records.")
        else:
            print("No duplicates found.")

if __name__ == "__main__":
    asyncio.run(delete_duplicates())
