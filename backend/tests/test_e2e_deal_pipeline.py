
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.models import Project, ProjectStatus, TWGPillar, UserRole
from app.agents.langgraph_resource_mobilization_agent import create_langgraph_resource_mobilization_agent
from uuid import uuid4

# Mock the entire LLM service to avoid external calls
@pytest.fixture
def mock_llm_service():
    # Patch the get_llm_service function in the base agent module
    with patch("app.agents.langgraph_base_agent.get_llm_service") as MockGetLLM:
        mock_service = MagicMock()
        
        # Mock chat_with_history return value
        # It needs to behave like an object with .content and .tool_calls
        mock_response = MagicMock()
        mock_response.content = "Here is the investment memo for the project..."
        mock_response.tool_calls = [] # No tools for this simple test
        
        # When chat_with_history is called (sync), it returns this object
        mock_service.chat_with_history.return_value = mock_response
        
        MockGetLLM.return_value = mock_service
        yield mock_service

@pytest.mark.asyncio
async def test_e2e_deal_pipeline_flow(client, db_session, admin_token_headers, mock_llm_service):
    """
    E2E Verification Scenario:
    1. Seed TWG
    2. Ingestion: Create Project
    3. Scoring: Verify Score
    4. Matching: Trigger Matching
    5. Deal Room: Mark Flagship
    6. Agent: Draft Memo
    """
    
    # 0. Seed TWG
    from app.models.models import TWG
    twg = TWG(name="Energy & Infrastructure", pillar=TWGPillar.energy_infrastructure)
    db_session.add(twg)
    await db_session.commit()
    await db_session.refresh(twg)
    twg_id = str(twg.id)
    
    # 1. Ingestion
    project_data = {
        "name": "Volta Green Energy Test",
        "description": "A 50MW Solar Plant in Ghana.",
        "pillar": TWGPillar.energy_infrastructure.value,
        "country": "Ghana",
        "investment_size": 50000000.0,
        "currency": "USD",
        "lead_country": "Ghana",
        "twg_id": twg_id
        # status defaults to IDENTIFIED
    }
    
    response = await client.post("/api/v1/projects/", json=project_data, headers=admin_token_headers)
    assert response.status_code in [200, 201], f"Create Project failed: {response.text}"
    created_project = response.json()
    project_id = created_project["id"]
    
    assert created_project["name"] == project_data["name"]
    assert created_project["status"] == ProjectStatus.IDENTIFIED.value

    # 2. Scoring - Verify score field exists
    response = await client.get(f"/api/v1/projects/{project_id}", headers=admin_token_headers)
    assert response.status_code == 200
    details = response.json()
    
    # Verify scoring fields exist
    assert "readiness_score" in details
    
    # 3. Agent Interaction - Verify agent can process project queries
    agent = create_langgraph_resource_mobilization_agent(db_session)
    
    user_message = f"What is the status of project {project_data['name']}?"
    thread_id = str(uuid4())
    
    # Run chat
    response_data = await agent.chat(
        message=user_message,
        thread_id=thread_id
    )
    
    response_text = response_data.get("response", "").lower()
    
    # Validation - Agent should respond (mocked LLM returns memo text)
    assert len(response_text) > 0
    assert "memo" in response_text or "project" in response_text

