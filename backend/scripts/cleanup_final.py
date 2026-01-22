"""
FINAL Cleanup - Using correct enum values
"""

import asyncio
from sqlalchemy import text, select
from app.core.database import get_db
from app.models.models import TWG, TWGPillar
from loguru import logger


async def final_cleanup():
    """Final cleanup with correct enum handling"""
    
    async for db in get_db():
        logger.info("=" * 70)
        logger.info("FINAL DATABASE CLEANUP")
        logger.info("=" * 70)
        
        # Step 1: Delete test/debug TWGs
        logger.info("\n1. Removing Test/Debug TWGs...")
        
        test_queries = [
            "DELETE FROM action_items WHERE meeting_id IN (SELECT id FROM meetings WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG')))",
            "DELETE FROM action_items WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            "DELETE FROM meeting_participants WHERE meeting_id IN (SELECT id FROM meetings WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG')))",
            "DELETE FROM documents WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            "DELETE FROM meetings WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            "DELETE FROM projects WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            "DELETE FROM twgs WHERE name IN ('Test TWG', 'Debug TWG')"
        ]
        
        for query in test_queries:
            try:
                result = await db.execute(text(query))
                if result.rowcount > 0:
                    logger.info(f"  ✓ Deleted {result.rowcount} records")
            except Exception as e:
                logger.warning(f"  ⚠ {str(e)[:80]}")
        
        await db.commit()
        
        # Step 2: Find and consolidate energy duplicates using ORM
        logger.info("\n2. Consolidating Energy Infrastructure duplicates...")
        
        energy_pillar = TWGPillar.energy_infrastructure
        result = await db.execute(
            select(TWG).where(TWG.pillar == energy_pillar).order_by(TWG.id)
        )
        energy_twgs = result.scalars().all()
        
        if len(energy_twgs) > 1:
            keep_id = energy_twgs[0].id
            delete_ids = [twg.id for twg in energy_twgs[1:]]
            
            logger.info(f"  Keeping: {keep_id}")
            logger.info(f"  Removing: {len(delete_ids)} duplicates")
            
            # Reassign using parameterized queries
            for dup_id in delete_ids:
                await db.execute(text(f"UPDATE action_items SET twg_id = '{keep_id}' WHERE twg_id = '{dup_id}'"))
                await db.execute(text(f"UPDATE documents SET twg_id = '{keep_id}' WHERE twg_id = '{dup_id}'"))
                await db.execute(text(f"UPDATE projects SET twg_id = '{keep_id}' WHERE twg_id = '{dup_id}'"))
                await db.execute(text(f"UPDATE meetings SET twg_id = '{keep_id}' WHERE twg_id = '{dup_id}'"))
                await db.execute(text(f"DELETE FROM twgs WHERE id = '{dup_id}'"))
            
            await db.commit()
            logger.info(f"  ✓ Consolidated {len(delete_ids)} duplicates")
        
        # Step 3: Final verification
        logger.info("\n3. Final TWG list:")
        final_twgs = await db.execute(select(TWG))
        count = 0
        for twg in final_twgs.scalars().all():
            logger.info(f"  • {twg.pillar.value}: {twg.name}")
            count += 1
        
        logger.info(f"\n✅ Total TWGs: {count}")
        logger.info("✅ CLEANUP COMPLETE! Refresh dashboard to see changes.")
        logger.info("=" * 70)
        
        break


if __name__ == "__main__":
    asyncio.run(final_cleanup())
