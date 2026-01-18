from celery import Celery
from app.core.config import settings

if settings.REDIS_URL:
    broker_url = settings.REDIS_URL
else:
    broker_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

celery_app = Celery("martin_worker", broker=broker_url)

celery_app.conf.task_routes = {
    "app.services.tasks.send_meeting_reminders": "periodic",
    "app.services.tasks.sync_rsvps": "periodic",
    "app.services.tasks.generate_project_pdf": "formatting",
    "app.services.scoring_tasks.rescore_project_async": "scoring",
}

celery_app.conf.beat_schedule = {
    "send-meeting-reminders-every-30-mins": {
        "task": "app.services.tasks.send_meeting_reminders",
        "schedule": 1800.0, # 30 minutes
    },
    "sync-rsvps-every-15-mins": {
        "task": "app.services.tasks.sync_rsvps",
        "schedule": 900.0, # 15 minutes
    },
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
