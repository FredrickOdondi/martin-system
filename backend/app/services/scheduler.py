from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.jobs.reminder_jobs import send_upcoming_meeting_reminders, check_missing_minutes
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        # Add jobs
        self.scheduler.add_job(
            send_upcoming_meeting_reminders,
            trigger=IntervalTrigger(hours=1),
            id="send_meeting_reminders",
            replace_existing=True
        )
        
        self.scheduler.add_job(
            check_missing_minutes,
            trigger=IntervalTrigger(hours=24), # Run daily
            id="check_missing_minutes",
            replace_existing=True
        )

        # Poll Google Drive for new meeting transcripts
        from app.services.drive_service import drive_service
        self.scheduler.add_job(
            drive_service.process_new_transcripts,
            trigger=IntervalTrigger(minutes=10),
            id="drive_transcript_poll",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("APScheduler started")
        
    def shutdown(self):
        self.scheduler.shutdown()
        logger.info("APScheduler shut down")

scheduler_service = SchedulerService()
