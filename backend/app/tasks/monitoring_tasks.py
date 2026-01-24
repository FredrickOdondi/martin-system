"""
Monitoring Tasks for Celery

These tasks replace the APScheduler jobs in continuous_monitor.py
Each task runs in isolation and won't block other tasks.
"""

from celery import shared_task
from loguru import logger
from app.core.database import get_db_session_context
from app.services.continuous_monitor import ContinuousMonitor


# Create a monitor instance for task execution
monitor = ContinuousMonitor()


@shared_task(
    name="app.tasks.monitoring_tasks.scan_scheduling_conflicts",
    rate_limit="2/m",  # Max 2 per minute
    max_retries=2,
    default_retry_delay=300,  # 5 minutes
)
def scan_scheduling_conflicts():
    """Scan for scheduling conflicts between meetings"""
    logger.info("Celery task: scan_scheduling_conflicts started")
    try:
        import asyncio
        asyncio.run(monitor.scan_scheduling_conflicts())
        logger.info("Celery task: scan_scheduling_conflicts completed")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Celery task: scan_scheduling_conflicts failed: {e}")
        raise


@shared_task(
    name="app.tasks.monitoring_tasks.scan_policy_divergences",
    rate_limit="1/h",  # Max 1 per hour (this is the expensive one)
    max_retries=2,
    default_retry_delay=600,  # 10 minutes
)
def scan_policy_divergences():
    """Scan for policy conflicts using LLM analysis"""
    logger.info("Celery task: scan_policy_divergences started")
    try:
        import asyncio
        asyncio.run(monitor.scan_policy_divergences())
        logger.info("Celery task: scan_policy_divergences completed")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Celery task: scan_policy_divergences failed: {e}")
        raise


@shared_task(
    name="app.tasks.monitoring_tasks.check_twg_health",
    rate_limit="1/h",  # Max 1 per hour
    max_retries=2,
)
def check_twg_health():
    """Check health status of all TWGs"""
    logger.info("Celery task: check_twg_health started")
    try:
        import asyncio
        asyncio.run(monitor.check_twg_health())
        logger.info("Celery task: check_twg_health completed")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Celery task: check_twg_health failed: {e}")
        raise


@shared_task(
    name="app.tasks.monitoring_tasks.scan_project_conflicts",
    rate_limit="1/6h",  # Max 1 per 6 hours
    max_retries=2,
)
def scan_project_conflicts():
    """Scan for project dependency and duplicate conflicts"""
    logger.info("Celery task: scan_project_conflicts started")
    try:
        import asyncio
        asyncio.run(monitor.scan_project_conflicts())
        logger.info("Celery task: scan_project_conflicts completed")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Celery task: scan_project_conflicts failed: {e}")
        raise


@shared_task(
    name="app.tasks.monitoring_tasks.check_upcoming_meetings",
    rate_limit="60/h",  # Max 60 per hour (1 per minute)
    max_retries=1,
)
def check_upcoming_meetings():
    """Check for upcoming meetings and dispatch Vexa bot"""
    logger.info("Celery task: check_upcoming_meetings started")
    try:
        import asyncio
        asyncio.run(monitor.check_upcoming_meetings())
        logger.info("Celery task: check_upcoming_meetings completed")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Celery task: check_upcoming_meetings failed: {e}")
        raise


@shared_task(
    name="app.tasks.monitoring_tasks.check_pending_transcripts",
    rate_limit="360/h",  # Max 360 per hour (6 per minute, every 10 seconds)
    max_retries=1,
)
def check_pending_transcripts():
    """Poll Vexa for pending transcripts"""
    logger.info("Celery task: check_pending_transcripts started")
    try:
        import asyncio
        asyncio.run(monitor.check_pending_transcripts())
        logger.info("Celery task: check_pending_transcripts completed")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Celery task: check_pending_transcripts failed: {e}")
        raise
