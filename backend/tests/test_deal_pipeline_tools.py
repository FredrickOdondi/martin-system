
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import uuid
from decimal import Decimal

from app.tools.deal_pipeline_tools import (
    get_project_details,
    list_flagship_projects,
    trigger_investor_matching,
    generate_investment_memo
)
from app.models.models import Project, ProjectStatus, TWGPillar, ProjectScoreDetail, ScoringCriteria

@pytest.fixture
def mock_db_session():
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    return mock_session

@pytest.fixture
def mock_get_db_context(mock_db_session):
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_db_session
    mock_ctx.__aexit__.return_value = None
    return mock_ctx

@pytest.fixture
def sample_project():
    return Project(
        id=uuid.uuid4(),
        name="Test Solar Farm",
        description="A large solar farm.",
        investment_size=Decimal("10000000.00"),
        currency="USD",
        status=ProjectStatus.DEAL_ROOM,
        pillar=TWGPillar.energy_infrastructure,
        is_flagship=True,
        readiness_score=8.5,
        afcen_score=Decimal("85.50"),
        lead_country="Ghana"
    )

@pytest.mark.asyncio
async def test_get_project_details(mock_db_session, sample_project):
    with patch("app.tools.deal_pipeline_tools.get_db_session_context") as mock_ctx_factory:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_db_session
        mock_ctx.__aexit__.return_value = None
        mock_ctx_factory.return_value = mock_ctx

        # Mock Project result
        mock_result_proj = MagicMock()
        mock_result_proj.scalars().first.return_value = sample_project
        
        # Mock Scores result
        mock_score_detail = ProjectScoreDetail(score=Decimal("9.0"), notes="Good")
        mock_criteria = ScoringCriteria(criterion_name="Feasibility")
        mock_result_scores = MagicMock()
        mock_result_scores.all.return_value = [(mock_score_detail, mock_criteria)]

        # Sequence of execute calls: 1. Project, 2. Scores
        mock_db_session.execute.side_effect = [mock_result_proj, mock_result_scores]

        result_json = await get_project_details(str(sample_project.id))
        result = json.loads(result_json)

        assert result["project"]["name"] == "Test Solar Farm"
        assert result["project"]["afcen_score"] == 85.5
        assert len(result["scores"]) == 1
        assert result["scores"][0]["criterion"] == "Feasibility"

@pytest.mark.asyncio
async def test_list_flagship_projects(mock_db_session, sample_project):
    with patch("app.tools.deal_pipeline_tools.get_db_session_context") as mock_ctx_factory:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_db_session
        mock_ctx_factory.return_value = mock_ctx

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [sample_project]
        mock_db_session.execute.return_value = mock_result

        result_json = await list_flagship_projects()
        result = json.loads(result_json)

        assert len(result) == 1
        assert result[0]["name"] == "Test Solar Farm"

@pytest.mark.asyncio
async def test_trigger_investor_matching(mock_db_session, sample_project):
    with patch("app.tools.deal_pipeline_tools.get_db_session_context") as mock_ctx_factory, \
         patch("app.tools.deal_pipeline_tools.get_investor_matching_service") as mock_service_factory:
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_db_session
        mock_ctx_factory.return_value = mock_ctx

        mock_service = AsyncMock()
        mock_service.match_investors.return_value = {"new_matches": 2}
        mock_service_factory.return_value = mock_service

        result_json = await trigger_investor_matching(str(sample_project.id))
        result = json.loads(result_json)

        assert result["new_matches"] == 2
        mock_service.match_investors.assert_called_once_with(str(sample_project.id))

@pytest.mark.asyncio
async def test_generate_investment_memo(sample_project):
    # Mock get_project_details to return valid JSON
    with patch("app.tools.deal_pipeline_tools.get_project_details") as mock_get_details, \
         patch("app.tools.deal_pipeline_tools.LLMService") as mock_llm_cls:
        
        mock_get_details.return_value = json.dumps({"project": {"name": "Test Project"}})
        
        mock_llm = AsyncMock()
        mock_llm.generate_text_async.return_value = "# Investment Memo\n\nExecutive Summary..."
        mock_llm_cls.return_value = mock_llm

        memo = await generate_investment_memo(str(sample_project.id))
        
        assert "# Investment Memo" in memo
        mock_llm.generate_text_async.assert_called_once()
