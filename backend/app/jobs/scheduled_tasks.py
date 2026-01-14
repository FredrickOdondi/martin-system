"""
Scheduled Tasks for Pipeline Automation

Event-driven triggers and scheduled jobs for:
1. Weekly Declaration Update (Mondays)
2. Weekly Progress Report (Sundays)  
3. Phase Completion Event Handler
"""

import logging
from datetime import datetime, timezone
from typing import Optional
import uuid

from app.core.database import get_db_session_context
from app.services.document_pipeline_service import DocumentPipelineService
from app.services.project_pipeline_service import ProjectPipelineService
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)


async def weekly_declaration_update():
    """
    Scheduled job: Runs every Monday to compile the weekly Declaration update.
    
    Triggers declaration synthesis with the 'weekly_update' milestone,
    gathering content from all TWG weekly packets.
    """
    logger.info("Running weekly_declaration_update job (Monday)")
    
    async with get_db_session_context() as db:
        try:
            pipeline = DocumentPipelineService(db)
            
            result = await pipeline.trigger_declaration_synthesis(
                milestone="weekly_update",
                title="ECOWAS Summit 2026 Declaration",
                preamble="Weekly consolidated update from all Technical Working Groups."
            )
            
            if result.get("error"):
                logger.warning(f"Declaration synthesis skipped: {result['error']}")
            else:
                logger.info(
                    f"✓ Weekly declaration update completed: version {result['version']}, "
                    f"document ID: {result['document'].id if result.get('document') else 'N/A'}"
                )
                
        except Exception as e:
            logger.error(f"Failed to run weekly declaration update: {e}")


async def weekly_progress_report():
    """
    Scheduled job: Runs every Sunday to generate the weekly progress report.
    
    Checks pipeline health and generates a summary of project statuses,
    identifying stalled projects and action items.
    """
    logger.info("Running weekly_progress_report job (Sunday)")
    
    async with get_db_session_context() as db:
        try:
            pipeline = ProjectPipelineService(db)
            
            health_report = await pipeline.check_pipeline_health()
            
            stalled_count = len(health_report.get("stalled_projects", []))
            healthy_count = health_report.get("healthy_projects", 0)
            total_count = health_report.get("total_projects", 0)
            
            logger.info(
                f"✓ Weekly progress report generated: "
                f"{total_count} total projects, "
                f"{healthy_count} healthy, "
                f"{stalled_count} stalled"
            )
            
            if stalled_count > 0:
                logger.warning(
                    f"Stalled projects requiring attention: "
                    f"{[p['name'] for p in health_report['stalled_projects']]}"
                )
                
            await audit_service.log_activity(
                db=db,
                user_id=None,
                action="weekly_progress_report",
                resource_type="pipeline",
                resource_id=None,
                details={
                    "total_projects": total_count,
                    "healthy_projects": healthy_count,
                    "stalled_projects": stalled_count,
                    "stalled_details": health_report.get("stalled_projects", []),
                    "by_stage": health_report.get("by_stage", {}),
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to run weekly progress report: {e}")


async def handle_phase_completion_event(
    phase_name: str,
    triggered_by_user_id: Optional[uuid.UUID] = None
):
    """
    Event handler: Triggered when a phase completion event occurs.
    
    Synthesizes a new declaration version capturing the milestone.
    
    Args:
        phase_name: Name of the completed phase (e.g., "Phase 1", "Preparation")
        triggered_by_user_id: Optional user ID who triggered the event
    """
    logger.info(f"Handling phase_completion event: {phase_name}")
    
    async with get_db_session_context() as db:
        try:
            pipeline = DocumentPipelineService(db)
            
            result = await pipeline.trigger_declaration_synthesis(
                milestone=f"phase_completion:{phase_name}",
                title="ECOWAS Summit 2026 Declaration",
                preamble=f"Milestone reached: {phase_name} completed.",
                triggered_by_user_id=triggered_by_user_id
            )
            
            if result.get("error"):
                logger.warning(f"Declaration synthesis skipped: {result['error']}")
            else:
                logger.info(
                    f"✓ Phase completion declaration generated: "
                    f"{phase_name}, version {result['version']}"
                )
                
        except Exception as e:
            logger.error(f"Failed to handle phase completion event: {e}")


class PipelineEventEmitter:
    """
    Simple event emitter for pipeline events.
    
    Allows triggering pipeline actions from other parts of the system.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners = {}
        return cls._instance
    
    def on(self, event_type: str, callback):
        """Register an event listener."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
        logger.debug(f"Registered listener for event: {event_type}")
    
    async def emit(self, event_type: str, **kwargs):
        """Emit an event to all registered listeners."""
        logger.info(f"Emitting event: {event_type}")
        listeners = self._listeners.get(event_type, [])
        for callback in listeners:
            try:
                await callback(**kwargs)
            except Exception as e:
                logger.error(f"Error in event listener for {event_type}: {e}")
    
    def remove_listener(self, event_type: str, callback):
        """Remove a specific event listener."""
        if event_type in self._listeners:
            self._listeners[event_type] = [
                cb for cb in self._listeners[event_type] if cb != callback
            ]


def get_pipeline_event_emitter() -> PipelineEventEmitter:
    """Get the singleton PipelineEventEmitter instance."""
    return PipelineEventEmitter()


def setup_event_listeners():
    """
    Initialize default event listeners.
    
    Call this during application startup to register
    the phase completion handler.
    """
    emitter = get_pipeline_event_emitter()
    emitter.on("phase_completion", handle_phase_completion_event)
    logger.info("Pipeline event listeners initialized")
