
import pytest
from unittest.mock import MagicMock, patch
from app.services.document_synthesizer import DocumentSynthesizer

def test_find_citation_uses_knowledge_base():
    """Verify that _find_citation calls the knowledge base search."""
    
    # Mock the Knowledge Base
    mock_kb = MagicMock()
    mock_kb.search.return_value = [
        {
            'id': 'doc1',
            'score': 0.85,
            'metadata': {'file_name': 'Energy Strategy 2026.pdf'}
        }
    ]
    
    # Patch the get_knowledge_base function to return our mock
    with patch('app.services.document_synthesizer.get_knowledge_base', return_value=mock_kb):
        synthesizer = DocumentSynthesizer()
        
        # Verify KB was attached
        assert synthesizer.kb == mock_kb
        
        # Test finding a citation
        citation = synthesizer._find_citation(
            claim="Energy demand will rise by 50%",
            knowledge_base={},
            twg_id="energy"
        )
        
        # Verify search was called with correct namespace
        mock_kb.search.assert_called_once()
        call_args = mock_kb.search.call_args
        assert call_args.kwargs['query'] == "Energy demand will rise by 50%"
        assert call_args.kwargs['namespace'] == "twg-energy"
        
        # Verify citation format
        assert citation == "Energy Strategy 2026.pdf"

def test_find_citation_fallback():
    """Verify that _find_citation falls back to dictionary if KB fails or returns nothing."""
    
    # Mock KB that returns empty results
    mock_kb = MagicMock()
    mock_kb.search.return_value = []
    
    with patch('app.services.document_synthesizer.get_knowledge_base', return_value=mock_kb):
        synthesizer = DocumentSynthesizer()
        
        # Test fallback with existing sources dict
        citation = synthesizer._find_citation(
            claim="Some claim",
            knowledge_base={"sources": {"energy": ["Fallback Source 2024"]}},
            twg_id="energy"
        )
        
        # Should return fallback
        assert citation == "Fallback Source 2024"
