import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.models import User, UserRole
from app.utils.security import hash_password

async def create_admin_user():
    email = "magwaro@ecowasiisummit.net"
    password = "TemporaryPassword123!" # Change this on first login!
    full_name = "Magwaro"
    
    async with AsyncSessionLocal() as session:
        # Check if user exists
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"User {email} already exists.")
            # Update role to ADMIN if not already
            if user.role != UserRole.ADMIN:
                print(f"Upgrading {email} to ADMIN...")
                user.role = UserRole.ADMIN
                await session.commit()
                print("Upgrade complete.")
            else:
                print("User is already an ADMIN.")
        else:
            print(f"Creating admin user {email}...")
            new_user = User(
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                role=UserRole.ADMIN,
                is_active=True,
                organization="ECOWAS Summit Secretariat"
            )
            session.add(new_user)
            await session.commit()
            print(f"User created successfully.")
            print(f"Email: {email}")
            print(f"Password: {password}")

if __name__ == "__main__":
    asyncio.run(create_admin_user())
