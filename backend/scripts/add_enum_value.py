import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def add_value():
    async with AsyncSessionLocal() as session:
        try:
            # Check if it exists first to avoid error
            result = await session.execute(text("SELECT unnest(enum_range(NULL::minutesstatus))"))
            values = result.scalars().all()
            if 'PENDING_APPROVAL' in values:
                print("PENDING_APPROVAL already exists.")
                return

            # Add value
            # Note: ALTER TYPE cannot be run inside a transaction block usually, 
            # but SQLAlchemy begins one implicitly.
            # So we might need to set isolation level or commit first.
            await session.execute(text("COMMIT")) # Ensure no transaction
            await session.execute(text("ALTER TYPE minutesstatus ADD VALUE 'PENDING_APPROVAL'"))
            print("Added PENDING_APPROVAL to minutesstatus.")
        except Exception as e:
            print(f"Error adding enum value: {e}")

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.getcwd())
    asyncio.run(add_value())
