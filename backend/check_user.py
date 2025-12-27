import asyncio
import uuid
import sys
from pathlib import Path

# Add the current directory to sys.path
sys.path.append(str(Path.cwd()))

from backend.app.core.database import SessionLocal
from backend.app.models.models import User

async def main():
    try:
        async with SessionLocal() as db:
            user_id = uuid.UUID('a6c34732-daa0-475a-bd22-beddd6e0cfad')
            user = await db.get(User, user_id)
            if user:
                print(f"FOUND: {user.full_name} ({user.email})")
            else:
                print("NOT_FOUND")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
