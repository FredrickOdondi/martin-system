"""
Tests for scheduled tasks and pipeline event handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import uuid

from app.jobs.scheduled_tasks import (
    weekly_declaration_update,
    weekly_progress_report,
    handle_phase_completion_event,
    get_pipeline_event_emitter,
    setup_event_listeners,
    PipelineEventEmitter,
)


class AsyncContextManager:
    """Helper for mocking async context manager."""
    def __init__(self, mock_session):
        self.mock_session = mock_session
    
    async def __aenter__(self):
        return self.mock_session
    
    async def __aexit__(self, *args):
        pass


@pytest.fixture
def mock_db_session():
    """Create a mock async database session."""
    return AsyncMock()


@pytest.fixture
def reset_event_emitter():
    """Reset the singleton event emitter between tests."""
    emitter = PipelineEventEmitter()
    emitter._listeners = {}
    yield
    emitter._listeners = {}


@pytest.mark.asyncio
async def test_weekly_declaration_update_triggers_synthesis(mock_db_session):
    """Test that weekly declaration update triggers document synthesis."""
    mock_result = {
        "document": MagicMock(id=uuid.uuid4()),
        "version": 1,
        "error": None
    }
    
    with patch('app.jobs.scheduled_tasks.get_db_session_context', return_value=AsyncContextManager(mock_db_session)):
        with patch('app.jobs.scheduled_tasks.DocumentPipelineService') as MockService:
            mock_service_instance = AsyncMock()
            mock_service_instance.trigger_declaration_synthesis.return_value = mock_result
            MockService.return_value = mock_service_instance
            
            await weekly_declaration_update()
            
            mock_service_instance.trigger_declaration_synthesis.assert_called_once_with(
                milestone="weekly_update",
                title="ECOWAS Summit 2026 Declaration",
                preamble="Weekly consolidated update from all Technical Working Groups."
            )


@pytest.mark.asyncio
async def test_weekly_declaration_update_handles_no_sections(mock_db_session):
    """Test that weekly declaration update handles case when no TWG sections available."""
    mock_result = {
        "document": None,
        "version": None,
        "error": "No TWG sections available for synthesis"
    }
    
    with patch('app.jobs.scheduled_tasks.get_db_session_context', return_value=AsyncContextManager(mock_db_session)):
        with patch('app.jobs.scheduled_tasks.DocumentPipelineService') as MockService:
            mock_service_instance = AsyncMock()
            mock_service_instance.trigger_declaration_synthesis.return_value = mock_result
            MockService.return_value = mock_service_instance
            
            # Should not raise, just log warning
            await weekly_declaration_update()


@pytest.mark.asyncio
async def test_weekly_progress_report_checks_pipeline_health(mock_db_session):
    """Test that weekly progress report runs pipeline health check."""
    mock_health = {
        "stalled_projects": [],
        "healthy_projects": 5,
        "total_projects": 5,
        "by_stage": {}
    }
    
    with patch('app.jobs.scheduled_tasks.get_db_session_context', return_value=AsyncContextManager(mock_db_session)):
        with patch('app.jobs.scheduled_tasks.ProjectPipelineService') as MockService:
            mock_service_instance = AsyncMock()
            mock_service_instance.check_pipeline_health.return_value = mock_health
            MockService.return_value = mock_service_instance
            
            with patch('app.jobs.scheduled_tasks.audit_service') as mock_audit:
                mock_audit.log_activity = AsyncMock()
                
                await weekly_progress_report()
                
                mock_service_instance.check_pipeline_health.assert_called_once()
                mock_audit.log_activity.assert_called_once()


@pytest.mark.asyncio
async def test_weekly_progress_report_logs_stalled_projects(mock_db_session):
    """Test that weekly progress report logs stalled projects."""
    mock_health = {
        "stalled_projects": [
            {"name": "Project A", "stage": "vetting", "days_in_stage": 30}
        ],
        "healthy_projects": 4,
        "total_projects": 5,
        "by_stage": {}
    }
    
    with patch('app.jobs.scheduled_tasks.get_db_session_context', return_value=AsyncContextManager(mock_db_session)):
        with patch('app.jobs.scheduled_tasks.ProjectPipelineService') as MockService:
            mock_service_instance = AsyncMock()
            mock_service_instance.check_pipeline_health.return_value = mock_health
            MockService.return_value = mock_service_instance
            
            with patch('app.jobs.scheduled_tasks.audit_service') as mock_audit:
                mock_audit.log_activity = AsyncMock()
                
                await weekly_progress_report()
                
                # Should have logged audit entry with stalled project info
                call_args = mock_audit.log_activity.call_args
                assert call_args[1]["details"]["stalled_projects"] == 1


@pytest.mark.asyncio
async def test_handle_phase_completion_event(mock_db_session):
    """Test phase completion event triggers declaration synthesis."""
    user_id = uuid.uuid4()
    mock_result = {
        "document": MagicMock(id=uuid.uuid4()),
        "version": 2,
        "error": None
    }
    
    with patch('app.jobs.scheduled_tasks.get_db_session_context', return_value=AsyncContextManager(mock_db_session)):
        with patch('app.jobs.scheduled_tasks.DocumentPipelineService') as MockService:
            mock_service_instance = AsyncMock()
            mock_service_instance.trigger_declaration_synthesis.return_value = mock_result
            MockService.return_value = mock_service_instance
            
            await handle_phase_completion_event(
                phase_name="Phase 1",
                triggered_by_user_id=user_id
            )
            
            mock_service_instance.trigger_declaration_synthesis.assert_called_once_with(
                milestone="phase_completion:Phase 1",
                title="ECOWAS Summit 2026 Declaration",
                preamble="Milestone reached: Phase 1 completed.",
                triggered_by_user_id=user_id
            )


def test_pipeline_event_emitter_singleton():
    """Test that PipelineEventEmitter is a singleton."""
    emitter1 = PipelineEventEmitter()
    emitter2 = PipelineEventEmitter()
    
    assert emitter1 is emitter2


def test_pipeline_event_emitter_register_listener(reset_event_emitter):
    """Test registering event listeners."""
    emitter = get_pipeline_event_emitter()
    callback = AsyncMock()
    
    emitter.on("test_event", callback)
    
    assert "test_event" in emitter._listeners
    assert callback in emitter._listeners["test_event"]


@pytest.mark.asyncio
async def test_pipeline_event_emitter_emit(reset_event_emitter):
    """Test emitting events to registered listeners."""
    emitter = get_pipeline_event_emitter()
    callback = AsyncMock()
    
    emitter.on("test_event", callback)
    await emitter.emit("test_event", param1="value1", param2="value2")
    
    callback.assert_called_once_with(param1="value1", param2="value2")


@pytest.mark.asyncio
async def test_pipeline_event_emitter_emit_no_listeners(reset_event_emitter):
    """Test emitting events when no listeners registered."""
    emitter = get_pipeline_event_emitter()
    
    # Should not raise
    await emitter.emit("nonexistent_event", data="test")


def test_pipeline_event_emitter_remove_listener(reset_event_emitter):
    """Test removing event listeners."""
    emitter = get_pipeline_event_emitter()
    callback = AsyncMock()
    
    emitter.on("test_event", callback)
    emitter.remove_listener("test_event", callback)
    
    assert callback not in emitter._listeners.get("test_event", [])


def test_setup_event_listeners_registers_phase_completion(reset_event_emitter):
    """Test that setup_event_listeners registers the phase completion handler."""
    emitter = get_pipeline_event_emitter()
    
    setup_event_listeners()
    
    assert "phase_completion" in emitter._listeners
    assert handle_phase_completion_event in emitter._listeners["phase_completion"]
