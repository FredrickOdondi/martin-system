"""
Negotiation Tasks for Celery

Handles conflict negotiation in isolated workers to prevent blocking.
"""

from celery import shared_task
from loguru import logger
from app.core.database import get_db_session_context
from app.services.negotiation_service import NegotiationService


@shared_task(
    name="app.tasks.negotiation_tasks.run_negotiation",
    rate_limit="5/m",  # Max 5 negotiations per minute to respect API limits
    max_retries=3,
    default_retry_delay=120,  # Wait 2 minutes before retry
    autoretry_for=(Exception,),
)
def run_negotiation_task(conflict_id: str):
    """
    Run negotiation for a conflict in isolated worker.
    
    Args:
        conflict_id: UUID of the conflict to negotiate
        
    Returns:
        dict: Negotiation result
    """
    logger.info(f"Celery task: run_negotiation started for conflict {conflict_id}")
    
    try:
        import asyncio
        
        async def _run():
            async with get_db_session_context() as db:
                negotiation_service = NegotiationService(db)
                result = await negotiation_service.run_negotiation(conflict_id)
                return result
        
        result = asyncio.run(_run())
        logger.info(f"Celery task: run_negotiation completed for conflict {conflict_id}")
        return result
        
    except Exception as e:
        logger.error(f"Celery task: run_negotiation failed for conflict {conflict_id}: {e}")
        # Check if it's a rate limit error
        if "429" in str(e) or "RateLimitReached" in str(e):
            logger.warning(f"Rate limit hit for conflict {conflict_id}, will retry after delay")
            # Celery will auto-retry with exponential backoff
        raise
