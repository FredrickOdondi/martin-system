import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.reconciliation_service import ReconciliationService
from app.models.models import Conflict, ConflictStatus

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.fixture
def reconciliation_service(mock_db_session):
    return ReconciliationService(mock_db_session)

@pytest.mark.asyncio
async def test_run_automated_negotiation_consensus(reconciliation_service, mock_db_session):
    # Setup mocks
    conflict = MagicMock(spec=Conflict)
    conflict.agents_involved = ["TWG1", "TWG2"]
    conflict.description = "Conflict A"
    conflict.resolution_log = []
    
    # Mock query_agent_constraints
    reconciliation_service.query_agent_constraints = AsyncMock(return_value={"priority": 5})
    
    # Mock supervisor_propose_resolution (returning 3 options)
    options = [
        {"id": 1, "action": "Option 1"},
        {"id": 2, "action": "Option 2"},
        {"id": 3, "action": "Option 3"}
    ]
    reconciliation_service.supervisor_propose_resolution = AsyncMock(return_value={"options": options})
    
    # Mock agents_evaluate_proposal (returning unanimous votes for Option 2)
    votes = {
        "TWG1": {"choice": 2, "reason": "Good"},
        "TWG2": {"choice": 2, "reason": "Also good"}
    }
    reconciliation_service.agents_evaluate_proposal = AsyncMock(return_value=votes)
    
    # Mock apply_meeting_resolution
    reconciliation_service.apply_meeting_resolution = AsyncMock(return_value={"success": True})
    
    # Execute
    result = await reconciliation_service.run_automated_negotiation(conflict)
    
    # Verify
    assert result["negotiation_result"] == "auto_resolved"
    assert result["consensus_reached"] is True
    assert result["winning_proposal"]["id"] == 2
    
    # Check that apply was called with winning option
    reconciliation_service.apply_meeting_resolution.assert_called_with(conflict, options[1])

@pytest.mark.asyncio
async def test_run_automated_negotiation_escalation(reconciliation_service, mock_db_session):
    # Setup mocks
    conflict = MagicMock(spec=Conflict)
    conflict.agents_involved = ["TWG1", "TWG2"]
    conflict.description = "Conflict B"
    conflict.resolution_log = []
    
    reconciliation_service.query_agent_constraints = AsyncMock(return_value={"priority": 5})
    
    options = [
        {"id": 1, "action": "Option 1"},
        {"id": 2, "action": "Option 2"}
    ]
    reconciliation_service.supervisor_propose_resolution = AsyncMock(return_value={"options": options})
    
    # Split votes
    votes = {
        "TWG1": {"choice": 1, "reason": "I want 1"},
        "TWG2": {"choice": 2, "reason": "I want 2"}
    }
    reconciliation_service.agents_evaluate_proposal = AsyncMock(return_value=votes)
    
    # Execute
    result = await reconciliation_service.run_automated_negotiation(conflict)
    
    # Verify
    assert result["negotiation_result"] == "escalated_to_human"
    assert result["consensus_reached"] is False
    assert conflict.status == ConflictStatus.ESCALATED
    
    # Verify DB commit for escalation
    mock_db_session.commit.assert_called()
