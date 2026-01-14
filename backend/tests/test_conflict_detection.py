
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

# Mocks for dependencies that might be hard to import
with patch.dict('sys.modules', {
    'app.core.database': MagicMock(),
    'app.core.config': MagicMock(),
}):
    from app.services.conflict_detector import ConflictDetector
    from app.models.models import Project, ConflictType, ConflictSeverity, ConflictStatus, Conflict

@pytest.mark.asyncio
async def test_detect_project_dependency_conflicts():
    # Setup
    detector = ConflictDetector()
    mock_db = AsyncMock()
    
    # Mock Projects
    p1 = Project(id=uuid.uuid4(), name="Solar Plant", description="Build solar plant", pillar="Energy", twg_id=uuid.uuid4())
    p2 = Project(id=uuid.uuid4(), name="Grid Extension", description="Extend grid to solar plant site", pillar="Infrastructure", twg_id=uuid.uuid4())
    
    # Mock DB result
    mock_result = MagicMock()
    # scalars().all() iteration
    mock_result.scalars.return_value.all.return_value = [p1, p2]
    mock_db.execute.return_value = mock_result
    
    # Mock LLM
    with patch('app.services.conflict_detector.get_llm_service') as mock_get_llm:
        mock_llm = MagicMock()
        # Return JSON string
        mock_llm.chat.return_value = '{"has_dependency": true, "dependency_type": "infrastructure", "confidence": 0.9, "reason": "Grid needed for solar", "estimated_delay_days": 100}'
        mock_get_llm.return_value = mock_llm
        
        # Run
        conflicts = await detector.detect_project_dependency_conflicts(mock_db)
        
        # Assert
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.PROJECT_DEPENDENCY_CONFLICT
        assert conflicts[0].severity == ConflictSeverity.HIGH
        assert conflicts[0].metadata_json['estimated_delay_days'] == 100
        print("\nTest Dependency Conflict: Passed")

@pytest.mark.asyncio
async def test_detect_duplicate_projects():
    # Setup
    detector = ConflictDetector()
    mock_db = AsyncMock()
    
    # Mock Projects
    p1 = Project(id=uuid.uuid4(), name="Solar Farm A", description="50MW solar", pillar="Energy", twg_id=uuid.uuid4(), lead_country="Mali")
    p2 = Project(id=uuid.uuid4(), name="Solar Plant B", description="50MW solar power station", pillar="Energy", twg_id=uuid.uuid4(), lead_country="Mali")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [p1, p2]
    mock_db.execute.return_value = mock_result
    
    # Mock KnowledgeBase
    with patch('app.services.conflict_detector.get_knowledge_base') as mock_get_kb:
        mock_kb = MagicMock()
        # Mock embeddings: identical vectors for high similarity
        # generate_embeddings returns list of vectors. 
        # called twice (once for cache loop, or maybe simpler).
        # My implementation loops projects and calls generate_embeddings([text])[0]
        # side_effect: return [[0.1, 0.2]] each time called
        mock_kb.generate_embeddings.side_effect = lambda x: [[0.1, 0.2]]
        mock_get_kb.return_value = mock_kb
        
        # Run
        conflicts = await detector.detect_duplicate_projects(mock_db)
        
        # Assert
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.DUPLICATE_PROJECT_CONFLICT
        assert conflicts[0].metadata_json['similarity_score'] >= 0.99
        print("\nTest Duplicate Conflict: Passed")
