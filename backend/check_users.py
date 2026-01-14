import asyncio
from app.database import get_db
from app.models import User
from sqlalchemy import select

async def check_users():
    async for db in get_db():
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f'Total users: {len(users)}')
        for u in users:
            print(f'- {u.email} ({u.full_name}) - Role: {u.role}')
        break

asyncio.run(check_users())
