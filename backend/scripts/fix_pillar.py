import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.database import get_db_session_context
from app.models.models import Project
from sqlalchemy import select, update

async def fix_project_pillar():
    async with get_db_session_context() as session:
        # Find project with null pillar but 'Infrastructure' in metadata (or just by name)
        stmt = select(Project).where(Project.name == "West African Regional Rail Upgrade")
        result = await session.execute(stmt)
        project = result.scalars().first()
        
        if project:
            print(f"Found project: {project.name}, Current Pillar: {project.pillar}")
            if not project.pillar or project.pillar == 'General':
                print("Fixing pillar to 'Infrastructure'...")
                project.pillar = "Infrastructure"
                
                # Check metadata just in case
                if project.metadata_json and project.metadata_json.get("pillar"):
                    print(f"Confirmed metadata has: {project.metadata_json.get('pillar')}")
                
                await session.commit()
                print("Pillar updated successfully.")
            else:
                print("Pillar is already set.")
        else:
            print("Project not found.")

if __name__ == "__main__":
    try:
        asyncio.run(fix_project_pillar())
    except Exception as e:
        print(f"Error: {e}")
