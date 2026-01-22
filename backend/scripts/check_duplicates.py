
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from app.core.config import settings
from app.models.models import Conflict

async def check_duplicates():
    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        # Group by description and count
        stmt = select(Conflict.description, func.count('*').label('count')).group_by(Conflict.description).having(func.count('*') > 1)
        result = await db.execute(stmt)
        duplicates = result.all()
        
        print(f"Found {len(duplicates)} descriptions with duplicates:")
        for desc, count in duplicates:
            print(f" - '{desc}': {count} copies")
            
        # Also check total count
        result = await db.execute(select(func.count(Conflict.id)))
        total = result.scalar()
        print(f"Total conflicts: {total}")

if __name__ == "__main__":
    asyncio.run(check_duplicates())
