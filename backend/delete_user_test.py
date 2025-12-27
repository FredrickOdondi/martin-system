import asyncio
import uuid
import sys
from pathlib import Path

# Add the root directory to sys.path
root_dir = Path.cwd().parent
sys.path.append(str(root_dir))

from backend.app.core.database import AsyncSessionLocal
from backend.app.models.models import User

async def main():
    user_id_str = 'a6c34732-daa0-475a-bd22-beddd6e0cfad'
    try:
        async with AsyncSessionLocal() as db:
            user_id = uuid.UUID(user_id_str)
            user = await db.get(User, user_id)
            if not user:
                print(f"User {user_id_str} not found.")
                return
            
            print(f"Attempting to delete user: {user.full_name}")
            await db.delete(user)
            await db.commit()
            print("SUCCESS: User deleted.")
    except Exception as e:
        print(f"FAILURE: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
