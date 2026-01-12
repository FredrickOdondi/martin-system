
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db_session_context
from app.models.models import User

async def check_user():
    async with get_db_session_context() as db:
        # List all users
        result = await db.execute(select(User).options(selectinload(User.twgs)).limit(20))
        users = result.scalars().all()
        
        print(f"Found {len(users)} users.")
        for user in users:
            print(f"User: {user.full_name}")
            print(f"Role: {user.role}")
            print(f"TWGs: {[twg.name for twg in user.twgs]}")
            print("---")

if __name__ == "__main__":
    asyncio.run(check_user())
