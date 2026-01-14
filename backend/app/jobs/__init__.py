"""
Jobs Package

Background jobs and scheduled tasks for the ECOWAS Summit system.
"""

from app.jobs.scheduled_tasks import (
    weekly_declaration_update,
    weekly_progress_report,
    handle_phase_completion_event,
    get_pipeline_event_emitter,
    setup_event_listeners,
)

__all__ = [
    "weekly_declaration_update",
    "weekly_progress_report",
    "handle_phase_completion_event",
    "get_pipeline_event_emitter",
    "setup_event_listeners",
]
