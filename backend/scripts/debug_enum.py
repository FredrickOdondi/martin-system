import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check_enum():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT enum_range(NULL::projectstatus)"))
        val = result.scalar()
        print(f"Current Enum Values: {val}")

if __name__ == "__main__":
    asyncio.run(check_enum())
