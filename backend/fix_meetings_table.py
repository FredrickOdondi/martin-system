import asyncio
from sqlalchemy import text
from app.core.database import engine

async def fix_table():
    queries = [
        "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS transcript TEXT"
    ]
    
    async with engine.begin() as conn:
        for q in queries:
            try:
                await conn.execute(text(q))
                print(f"Executed: {q}")
            except Exception as e:
                print(f"Failed: {q} - {e}")

if __name__ == "__main__":
    asyncio.run(fix_table())
