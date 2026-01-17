"""
COMPREHENSIVE SQL Cleanup - Delete in correct dependency order
"""

import asyncio
from sqlalchemy import text
from app.core.database import get_db
from loguru import logger


async def comprehensive_sql_cleanup():
    """Delete in correct dependency order"""
    
    async for db in get_db():
        logger.info("=" * 70)
        logger.info("COMPREHENSIVE DATABASE CLEANUP")
        logger.info("=" * 70)
        
        # Delete in reverse dependency order:
        # action_items -> meetings/projects/documents -> twgs
        
        logger.info("\n1. Deleting ALL data for Test/Debug TWGs...")
        
        cleanup_queries = [
            # First: action_items (depends on meetings, projects, documents)
            "DELETE FROM action_items WHERE meeting_id IN (SELECT id FROM meetings WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG')))",
            "DELETE FROM action_items WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            
            # Second: meeting participants, documents, etc
            "DELETE FROM meeting_participants WHERE meeting_id IN (SELECT id FROM meetings WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG')))",
            "DELETE FROM documents WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            
            # Third: meetings and projects
            "DELETE FROM meetings WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            "DELETE FROM projects WHERE twg_id IN (SELECT id FROM twgs WHERE name IN ('Test TWG', 'Debug TWG'))",
            
            # Finally: TWGs themselves
            "DELETE FROM twgs WHERE name IN ('Test TWG', 'Debug TWG')"
        ]
        
        for query in cleanup_queries:
            try:
                result = await db.execute(text(query))
                logger.info(f"  ✓ {query[:70]}... ({result.rowcount} rows)")
            except Exception as e:
                logger.warning(f"  ⚠ Query failed (may be expected): {str(e)[:100]}")
        
        await db.commit()
        logger.info("  ✓ Test/Debug TWGs removed")
        
        # Step 2: Consolidate Energy duplicates
        logger.info("\n2. Consolidating Energy Infrastructure duplicates...")
        
        first_energy_result = await db.execute(
            text("SELECT id FROM twgs WHERE pillar = 'TWGPillar.energy_infrastructure' ORDER BY id LIMIT 1")
        )
        first_energy_id = first_energy_result.scalar()
        
        if first_energy_id:
            logger.info(f"  Keeping Energy TWG: {first_energy_id}")
            
            # Reassign in correct order
            reassign_queries = [
                # First: action_items
                f"UPDATE action_items SET twg_id = '{first_energy_id}' WHERE twg_id IN (SELECT id FROM twgs WHERE pillar = 'TWGPillar.energy_infrastructure' AND id != '{first_energy_id}')",
                
                # Then: documents, projects, meetings
                f"UPDATE documents SET twg_id = '{first_energy_id}' WHERE twg_id IN (SELECT id FROM twgs WHERE pillar = 'TWGPillar.energy_infrastructure' AND id != '{first_energy_id}')",
                f"UPDATE projects SET twg_id = '{first_energy_id}' WHERE twg_id IN (SELECT id FROM twgs WHERE pillar = 'TWGPillar.energy_infrastructure' AND id != '{first_energy_id}')",
                f"UPDATE meetings SET twg_id = '{first_energy_id}' WHERE twg_id IN (SELECT id FROM twgs WHERE pillar = 'TWGPillar.energy_infrastructure' AND id != '{first_energy_id}')",
            ]
            
            for query in reassign_queries:
                result = await db.execute(text(query))
                if result.rowcount > 0:
                    logger.info(f"  ✓ Reassigned {result.rowcount} records")
            
            # Delete duplicates
            delete_result = await db.execute(
                text(f"DELETE FROM twgs WHERE pillar = 'TWGPillar.energy_infrastructure' AND id != '{first_energy_id}'")
            )
            logger.info(f"  ✓ Deleted {delete_result.rowcount} duplicate Energy TWGs")
        
        await db.commit()
        
        # Step 3: Verify
        logger.info("\n3. Final TWG list:")
        final_result = await db.execute(text("SELECT pillar, name FROM twgs ORDER BY pillar"))
        count = 0
        for row in final_result:
            logger.info(f"  • {row[0]}: {row[1]}")
            count += 1
        
        logger.info(f"\nTotal TWGs: {count}")
        logger.info("\n" + "=" * 70)
        logger.info("✅ CLEANUP COMPLETE! Agent routing should now work.")
        logger.info("=" * 70)
        
        break


if __name__ == "__main__":
    asyncio.run(comprehensive_sql_cleanup())
