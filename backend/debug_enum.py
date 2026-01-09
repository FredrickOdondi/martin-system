import asyncio
from sqlalchemy import text
from app.core.database import get_db, AsyncSessionLocal

async def check_enum():
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text("SELECT unnest(enum_range(NULL::minutesstatus))"))
            values = result.scalars().all()
            print(f"Allowed MinutesStatus values in DB: {values}")
        except Exception as e:
            print(f"Error checking enum: {e}")

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.getcwd())
    asyncio.run(check_enum())
