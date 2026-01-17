"""
COMPREHENSIVE Database Cleanup - Handle ALL Foreign Keys

Foreign key constraints found:
- projects.twg_id -> twgs.id
- documents.twg_id -> twgs.id  
- meetings.twg_id -> twgs.id (possibly)

Strategy:
1. Reassign ALL related records to the kept TWG
2. Then delete duplicate TWGs
"""

import asyncio
from sqlalchemy import select, func, delete, update
from app.core.database import get_db
from app.models.models import TWG, Project, Meeting, Document
from loguru import logger


async def comprehensive_cleanup():
    """Comprehensive cleanup handling all foreign keys"""
    
    async for db in get_db():
        logger.info("=" * 70)
        logger.info("COMPREHENSIVE DATABASE CLEANUP - REMOVING DUPLICATE TWGs")
        logger.info("=" * 70)
        
        # 1. Identify duplicates
        logger.info("\n📊 Step 1: Analyzing TWG records...")
        
        result = await db.execute(select(TWG).order_by(TWG.id))
        all_twgs = result.scalars().all()
        
        pillar_map = {}  # pillar -> (keep_id, [delete_ids])
        
        for twg in all_twgs:
            if twg.pillar not in pillar_map:
                pillar_map[twg.pillar] = (twg.id, [])
                logger.info(f"  ✓ KEEP: {twg.pillar} (ID: {str(twg.id)[:8]}...)")
            else:
                pillar_map[twg.pillar][1].append(twg.id)
                logger.warning(f"  ✗ DUP:  {twg.pillar} (ID: {str(twg.id)[:8]}...)")
        
        # 2. Reassign ALL related records
        for pillar, (keep_id, delete_ids) in pillar_map.items():
            if not delete_ids:
                continue
                
            logger.info(f"\n🔄 Step 2: Reassigning records for {pillar}...")
            
            for dup_id in delete_ids:
                # Reassign projects
                proj_count = await db.scalar(
                    select(func.count(Project.id)).where(Project.twg_id == dup_id)
                )
                if proj_count > 0:
                    await db.execute(
                        update(Project).where(Project.twg_id == dup_id).values(twg_id=keep_id)
                    )
                    logger.info(f"  ✓ Reassigned {proj_count} projects")
                
                # Reassign documents
                doc_count = await db.scalar(
                    select(func.count(Document.id)).where(Document.twg_id == dup_id)
                )
                if doc_count > 0:
                    await db.execute(
                        update(Document).where(Document.twg_id == dup_id).values(twg_id=keep_id)
                    )
                    logger.info(f"  ✓ Reassigned {doc_count} documents")
                
                # Reassign meetings (if they have twg_id)
                try:
                    meet_count = await db.scalar(
                        select(func.count(Meeting.id)).where(Meeting.twg_id == dup_id)
                    )
                    if meet_count > 0:
                        await db.execute(
                            update(Meeting).where(Meeting.twg_id == dup_id).values(twg_id=keep_id)
                        )
                        logger.info(f"  ✓ Reassigned {meet_count} meetings")
                except Exception:
                    pass  # meetings might not have twg_id
            
            await db.commit()
        
        # 3. Delete duplicates
        all_delete_ids = []
        for pillar, (keep_id, delete_ids) in pillar_map.items():
            all_delete_ids.extend(delete_ids)
        
        if all_delete_ids:
            logger.info(f"\n🗑️  Step 3: Deleting {len(all_delete_ids)} duplicate TWGs...")
            await db.execute(delete(TWG).where(TWG.id.in_(all_delete_ids)))
            await db.commit()
            logger.info(f"  ✓ Successfully deleted {len(all_delete_ids)} duplicates!")
        
        # 4. Verify cleanup
        logger.info("\n📈 Step 4: Final database state:")
        twg_count = await db.scalar(select(func.count(TWG.id)))
        project_count = await db.scalar(select(func.count(Project.id)))
        meeting_count = await db.scalar(select(func.count(Meeting.id)))
        doc_count = await db.scalar(select(func.count(Document.id)))
        
        logger.info(f"  TWGs: {twg_count}")
        logger.info(f"  Projects: {project_count}")
        logger.info(f"  Meetings: {meeting_count}")
        logger.info(f"  Documents: {doc_count}")
        
        logger.info("\n📋 Final TWG list:")
        final_twgs = await db.execute(select(TWG))
        for twg in final_twgs.scalars().all():
            logger.info(f"  • {twg.pillar}: {twg.name}")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ CLEANUP COMPLETE!")
        logger.info("   Agent routing errors should now be resolved.")
        logger.info("=" * 70)
        
        break


if __name__ == "__main__":
    asyncio.run(comprehensive_cleanup())
