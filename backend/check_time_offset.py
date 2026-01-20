import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.models import Meeting
from datetime import datetime

async def check_time():
    async with AsyncSessionLocal() as db:
        print(f"Current UTC Time: {datetime.utcnow()}")
        
        # Find meetings today
        stmt = select(Meeting).where(Meeting.title.ilike("%Policy%")) # Using part of title from screenshot? "Policy Framework 2026"
        # Or just get all future
        result = await db.execute(stmt)
        meetings = result.scalars().all()
        
        for m in meetings:
            print(f"Meeting: '{m.title}' (ID: {m.id})")
            print(f"  - Scheduled: {m.scheduled_at}")
            print(f"  - Location: '{m.location}'")
            print(f"  - Transcript: {repr(m.transcript)}")
            
            # Check logic explicitly
            if m.location and "meet.google.com" in m.location:
                 print("  => VALID LINK")
            else:
                 print("  => INVALID/MISSING LINK")
                 
            if m.transcript is None:
                 print("  => TRANSCRIPT IS NONE (Ready to record)")
            else:
                 print("  => TRANSCRIPT EXISTS (Skipping)")
            
            # Calc diff
            now_utc = datetime.utcnow()
            diff = m.scheduled_at - now_utc
            print(f"  - Diff from UTC Now: {diff}")
            
            if 0 <= diff.total_seconds() <= 600:
                print("  => MATCHES QUERY WINDOW (0-10 min)")
            else:
                print("  => FAILS QUERY WINDOW")

if __name__ == "__main__":
    asyncio.run(check_time())
