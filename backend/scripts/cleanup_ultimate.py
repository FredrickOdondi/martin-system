"""
ULTIMATE Database Cleanup - Handle ALL Foreign Keys

This script will:
1. Delete ALL test/debug TWGs and their related data
2. Consolidate duplicate Energy TWGs
3. Handle ALL foreign key dependencies in correct order
"""

import asyncio
from sqlalchemy import text, select
from app.core.database import get_db
from app.models.models import TWG, TWGPillar
from loguru import logger


async def ultimate_cleanup():
    """Ultimate cleanup handling all dependencies"""
    
    async for db in get_db():
        logger.info("=" * 70)
        logger.info("ULTIMATE DATABASE CLEANUP - REMOVING ALL DUPLICATES")
        logger.info("=" * 70)
        
        # Step 1: Delete Test/Debug TWGs and ALL related data
        logger.info("\n📋 Step 1: Removing Test/Debug TWGs...")
        
        # Delete in correct dependency order (deepest dependencies first)
        test_cleanup = [
            # Level 4: Deepest dependencies
            "DELETE FROM action_items WHERE meeting_id IN (SELECT id FROM meetings WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG')))",
            
            # Level 3: Mid-level dependencies
            "DELETE FROM action_items WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            "DELETE FROM meeting_participants WHERE meeting_id IN (SELECT id FROM meetings WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG')))",
            "DELETE FROM weekly_packets WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            
            # Level 2: Direct TWG dependencies
            "DELETE FROM documents WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            "DELETE FROM projects WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            "DELETE FROM meetings WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            
            # Level 1: TWGs themselves
            "DELETE FROM twgs WHERE name IN ('Test TWG', 'Debug TWG')"
        ]
        
        total_deleted = 0
        for query in test_cleanup:
            try:
                result = await db.execute(text(query))
                if result.rowcount > 0:
                    logger.info(f"  ✓ Deleted {result.rowcount} records")
                    total_deleted += result.rowcount
            except Exception as e:
                logger.warning(f"  ⚠ {str(e)[:100]}")
        
        await db.commit()
        logger.info(f"  ✅ Removed {total_deleted} test/debug records")
        
        # Step 2: Consolidate Energy Infrastructure duplicates
        logger.info("\n🔄 Step 2: Consolidating Energy Infrastructure duplicates...")
        
        energy_pillar = TWGPillar.energy_infrastructure
        result = await db.execute(
            select(TWG).where(TWG.pillar == energy_pillar).order_by(TWG.id)
        )
        energy_twgs = result.scalars().all()
        
        if len(energy_twgs) > 1:
            keep_id = energy_twgs[0].id
            delete_ids = [str(twg.id) for twg in energy_twgs[1:]]
            
            logger.info(f"  Keeping: {keep_id} ({energy_twgs[0].name})")
            logger.info(f"  Removing: {len(delete_ids)} duplicates")
            
            # Reassign ALL related records
            for dup_id in delete_ids:
                reassign_queries = [
                    # Reassign weekly_packets
                    f"UPDATE weekly_packets SET twg_id = '{keep_id}' WHERE twg_id = '{dup_id}'",
                    # Reassign action_items
                    f"UPDATE action_items SET twg_id = '{keep_id}' WHERE twg_id = '{dup_id}'",
                    # Reassign documents
                    f"UPDATE documents SET twg_id = '{keep_id}' WHERE twg_id = '{dup_id}'",
                    # Reassign projects
                    f"UPDATE projects SET twg_id = '{keep_id}' WHERE twg_id = '{dup_id}'",
                    # Reassign meetings
                    f"UPDATE meetings SET twg_id = '{keep_id}' WHERE twg_id = '{dup_id}'",
                ]
                
                for query in reassign_queries:
                    try:
                        result = await db.execute(text(query))
                        if result.rowcount > 0:
                            logger.info(f"    ✓ Reassigned {result.rowcount} records from {dup_id[:8]}...")
                    except Exception as e:
                        logger.warning(f"    ⚠ {str(e)[:80]}")
                
                # Now delete the duplicate TWG
                await db.execute(text(f"DELETE FROM twgs WHERE id = '{dup_id}'"))
                logger.info(f"    ✓ Deleted duplicate TWG {dup_id[:8]}...")
            
            await db.commit()
            logger.info(f"  ✅ Consolidated {len(delete_ids)} Energy TWG duplicates")
        else:
            logger.info("  ✓ No Energy TWG duplicates found")
        
        # Step 3: Final verification
        logger.info("\n📊 Step 3: Final database state:")
        
        final_twgs = await db.execute(select(TWG).order_by(TWG.pillar))
        count = 0
        for twg in final_twgs.scalars().all():
            logger.info(f"  • {twg.pillar.value}: {twg.name} (ID: {str(twg.id)[:8]}...)")
            count += 1
        
        logger.info(f"\n✅ Total TWGs: {count}")
        logger.info("\n" + "=" * 70)
        logger.info("✅ CLEANUP COMPLETE!")
        logger.info("   Refresh your dashboard to see the clean TWG list.")
        logger.info("=" * 70)
        
        break


if __name__ == "__main__":
    asyncio.run(ultimate_cleanup())
