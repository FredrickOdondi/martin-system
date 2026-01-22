"""
SIMPLE Cleanup - Delete Test/Debug TWGs Only

Strategy: Just delete the obviously test TWGs (Test TWG, Debug TWG)
Leave the energy duplicates for manual review since they may have real data.
"""

import asyncio
from sqlalchemy import select, delete, text
from app.core.database import get_db
from app.models.models import TWG
from loguru import logger


async def simple_cleanup():
    """Delete only test/debug TWGs"""
    
    async for db in get_db():
        logger.info("=" * 70)
        logger.info("SIMPLE CLEANUP - Removing Test/Debug TWGs")
        logger.info("=" * 70)
        
        # Find test TWGs
        result = await db.execute(
            select(TWG).where(
                TWG.name.in_(['Test TWG', 'Debug TWG'])
            )
        )
        test_twgs = result.scalars().all()
        
        logger.info(f"\nFound {len(test_twgs)} test/debug TWGs:")
        for twg in test_twgs:
            logger.info(f"  - {twg.name} (ID: {str(twg.id)[:8]}...)")
        
        if test_twgs:
            test_ids = [twg.id for twg in test_twgs]
            
            # Use CASCADE delete via raw SQL
            logger.info(f"\nDeleting {len(test_ids)} test TWGs with CASCADE...")
            for twg_id in test_ids:
                await db.execute(
                    text("DELETE FROM twgs WHERE id = :id"),
                    {"id": str(twg_id)}
                )
            
            await db.commit()
            logger.info(f"✓ Deleted {len(test_ids)} test/debug TWGs")
        
        # Show remaining TWGs
        logger.info("\n📋 Remaining TWGs:")
        remaining = await db.execute(select(TWG))
        for twg in remaining.scalars().all():
            logger.info(f"  • {twg.pillar}: {twg.name}")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ CLEANUP COMPLETE!")
        logger.info("=" * 70)
        
        break


if __name__ == "__main__":
    asyncio.run(simple_cleanup())
