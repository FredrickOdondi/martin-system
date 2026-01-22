"""
Database Cleanup Script - Investigate Duplicates and Test Data
"""

import asyncio
from sqlalchemy import select, func, text
from app.core.database import get_db
from app.models.models import TWG, Project, Meeting, User, Document
from loguru import logger


async def investigate_duplicates():
    """Find duplicate TWG records and other test data"""
    
    async for db in get_db():
        # 1. Find duplicate TWGs by pillar
        logger.info("=" * 60)
        logger.info("INVESTIGATING DUPLICATE TWGs")
        logger.info("=" * 60)
        
        result = await db.execute(
            select(TWG.pillar, func.count(TWG.id).label('count'))
            .group_by(TWG.pillar)
            .having(func.count(TWG.id) > 1)
        )
        duplicates = result.all()
        
        if duplicates:
            logger.warning(f"Found {len(duplicates)} duplicate pillar(s):")
            for pillar, count in duplicates:
                logger.warning(f"  - {pillar}: {count} records")
                
                # Get details of duplicates
                twg_result = await db.execute(
                    select(TWG).where(TWG.pillar == pillar)
                )
                twgs = twg_result.scalars().all()
                
                for twg in twgs:
                    logger.info(f"    ID: {twg.id}, Name: {twg.name}, Created: {twg.created_at}")
        else:
            logger.info("No duplicate TWGs found")
        
        # 2. Count all records
        logger.info("\n" + "=" * 60)
        logger.info("DATABASE RECORD COUNTS")
        logger.info("=" * 60)
        
        twg_count = await db.scalar(select(func.count(TWG.id)))
        project_count = await db.scalar(select(func.count(Project.id)))
        meeting_count = await db.scalar(select(func.count(Meeting.id)))
        user_count = await db.scalar(select(func.count(User.id)))
        doc_count = await db.scalar(select(func.count(Document.id)))
        
        logger.info(f"TWGs: {twg_count}")
        logger.info(f"Projects: {project_count}")
        logger.info(f"Meetings: {meeting_count}")
        logger.info(f"Users: {user_count}")
        logger.info(f"Documents: {doc_count}")
        
        # 3. List all TWGs
        logger.info("\n" + "=" * 60)
        logger.info("ALL TWG RECORDS")
        logger.info("=" * 60)
        
        all_twgs = await db.execute(select(TWG))
        for twg in all_twgs.scalars().all():
            logger.info(f"ID: {twg.id}, Pillar: {twg.pillar}, Name: {twg.name}")
        
        # 4. Sample meetings (first 10)
        logger.info("\n" + "=" * 60)
        logger.info("SAMPLE MEETINGS (first 10)")
        logger.info("=" * 60)
        
        meetings = await db.execute(select(Meeting).limit(10))
        for meeting in meetings.scalars().all():
            logger.info(f"ID: {meeting.id}, Title: {meeting.title}, Date: {meeting.scheduled_date}")
        
        break  # Only need one iteration


if __name__ == "__main__":
    asyncio.run(investigate_duplicates())
