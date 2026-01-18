"""
Celery tasks for project scoring operations.

This module contains background tasks for recalculating AfCEN scores
when project-related changes occur (document uploads/deletes, project updates, etc.)
"""
import asyncio
from typing import Dict, Any
from loguru import logger
from uuid import UUID

from app.core.celery_app import celery_app
from app.core.database import get_db_session_context


@celery_app.task(bind=True, max_retries=3)
def rescore_project_async(self, project_id: str) -> Dict[str, Any]:
    """
    Background task to recalculate project AfCEN score.
    
    This task is triggered when:
    - Documents are uploaded to a project
    - Documents are deleted from a project
    - Project details are updated
    - Project status changes
    
    Args:
        project_id: UUID string of the project to rescore
        
    Returns:
        Dict with project_id and new score, or error details
    """
    try:
        logger.info(f"Starting AfCEN scoring for project {project_id}")
        
        # Run async scoring in sync context
        async def run_scoring():
            from app.services.project_pipeline_service import ProjectPipelineService
            
            async with get_db_session_context() as db:
                service = ProjectPipelineService(db)
                score = await service.assess_project_readiness(UUID(project_id))
                return score
        
        # Execute async function
        score = asyncio.run(run_scoring())
        
        logger.info(f"✓ Rescored project {project_id}: AfCEN Score = {score}")
        
        return {
            "status": "success",
            "project_id": project_id,
            "afcen_score": float(score)
        }
        
    except Exception as e:
        logger.error(f"Scoring failed for project {project_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60)
