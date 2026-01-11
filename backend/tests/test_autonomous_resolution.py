import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.continuous_monitor import ContinuousMonitor
from app.models.models import ConflictStatus
from datetime import datetime, UTC

@pytest.fixture
def monitor():
    return ContinuousMonitor()

@pytest.mark.asyncio
async def test_handle_detected_conflicts_triggers_negotiation(monitor):
    # Setup mocks
    session = AsyncMock()
    
    # Mock Conflict object creation
    with patch('app.services.continuous_monitor.Conflict') as MockConflict:
        mock_conflict_instance = MagicMock()
        mock_conflict_instance.id = "conflict-123"
        MockConflict.return_value = mock_conflict_instance
        
        # Mock ReconciliationService
        with patch('app.services.continuous_monitor.get_reconciliation_service') as mock_get_service:
            mock_reconciler = AsyncMock()
            mock_get_service.return_value = mock_reconciler
            
            # Mock negotiation result
            mock_reconciler.run_automated_negotiation.return_value = {
                "negotiation_result": "auto_resolved",
                "proposal": {"action": "Shift meeting"}
            }
            
            # Execute
            conflict_data = {
                "description": "Test Conflict",
                "conflict_type": "temporal",
                "severity": "high"
            }
            agents = ["twg1", "twg2"]
            
            await monitor._handle_detected_conflicts(session, conflict_data, agents)
            
            # Verify Conflict Creation
            assert MockConflict.called
            assert session.add.called
            
            # Verify Trigger
            assert mock_get_service.called
            assert mock_reconciler.run_automated_negotiation.called
            mock_reconciler.run_automated_negotiation.assert_called_with(mock_conflict_instance)
            
            # Verify Commit
            assert session.commit.called

@pytest.mark.asyncio
async def test_scan_scheduling_conflicts_calls_handler(monitor):
    # Setup mocks similar to previous tests but checking for handler call
    session = AsyncMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=None)
    
    with patch('app.services.continuous_monitor.get_db_session_context', return_value=cm):
        # Mock overlapping meetings
        m1 = MagicMock()
        m1.scheduled_at = datetime(2026, 3, 1, 10, 0, tzinfo=UTC)
        m1.duration_minutes = 120
        m1.venue = "Room A"
        m1.title = "M1"
        m1.twg_id = "twg1"
        
        m2 = MagicMock()
        m2.scheduled_at = datetime(2026, 3, 1, 11, 0, tzinfo=UTC)
        m2.duration_minutes = 120
        m2.venue = "Room A"
        m2.title = "M2"
        m2.twg_id = "twg2"
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [m1, m2]
        session.execute.return_value = mock_result
        
        # Mock _handle_detected_conflicts
        with patch.object(monitor, '_handle_detected_conflicts', new_callable=AsyncMock) as mock_handle:
            await monitor.scan_scheduling_conflicts()
            
            assert mock_handle.called
            # Verify arguments
            args = mock_handle.call_args
            assert args.kwargs['conflict_data']['conflict_type'] == "temporal"
            assert set(args.kwargs['agents_involved']) == {"twg1", "twg2"}
