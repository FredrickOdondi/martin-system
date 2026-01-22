"""
Manual script to seed default scoring criteria.
Run this to populate the ScoringCriteria table.
"""

import asyncio
from sqlalchemy import select
from decimal import Decimal

# Add parent directory to path
import sys
sys.path.insert(0, '/home/evan/Desktop/martin os v2/martin-system/backend')

from app.core.database import get_db_session_context
from app.models.models import ScoringCriteria


async def seed_criteria():
    """Seed default scoring criteria."""
    
    async with get_db_session_context() as db:
        # Check if criteria already exist
        result = await db.execute(select(ScoringCriteria))
        existing = result.scalars().all()
        
        if existing:
            print(f"✓ Found {len(existing)} existing criteria:")
            for c in existing:
                print(f"  - {c.criterion_name} ({c.criterion_type})")
            return
        
        print("No criteria found. Seeding defaults...")
        
        defaults = [
            {"name": "Feasibility Study", "type": "readiness", "weight": 2.0, "desc": "Completed Feasibility Study"},
            {"name": "ESIA", "type": "readiness", "weight": 2.0, "desc": "Environmental & Social Impact Assessment"},
            {"name": "Financial Model", "type": "readiness", "weight": 2.0, "desc": "Robust Financial Model"},
            {"name": "Site Control", "type": "readiness", "weight": 2.0, "desc": "Land/Site Access Secured"},
            {"name": "Permits", "type": "readiness", "weight": 2.0, "desc": "Key Permits Obtained"},
            {"name": "Gov Support", "type": "strategic_fit", "weight": 5.0, "desc": "Letter of Government Support"},
            {"name": "Regional Integration", "type": "strategic_fit", "weight": 5.0, "desc": "Cross-border benefits"},
        ]
        
        for d in defaults:
            criterion = ScoringCriteria(
                criterion_name=d["name"],
                criterion_type=d["type"],
                weight=Decimal(str(d["weight"])),
                description=d["desc"]
            )
            db.add(criterion)
            print(f"  + Added: {d['name']}")
        
        await db.commit()
        print(f"\n✓ Successfully seeded {len(defaults)} criteria!")


if __name__ == "__main__":
    asyncio.run(seed_criteria())
