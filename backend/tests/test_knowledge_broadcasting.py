import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json
import uuid

from app.services.broadcast_service import BroadcastService
from app.models.models import Document

@pytest.fixture
def mock_redis():
    with patch('app.services.broadcast_service.redis.Redis') as mock:
        yield mock

@pytest.fixture
def mock_kb():
    with patch('app.services.broadcast_service.get_knowledge_base') as mock:
        yield mock

def test_broadcast_document(mock_redis, mock_kb):
    # Setup mocks
    mock_redis_instance = MagicMock()
    mock_redis.from_url.return_value = mock_redis_instance
    
    mock_kb_instance = MagicMock()
    mock_kb.return_value = mock_kb_instance
    
    service = BroadcastService()
    # Force redis client inject if needed (init might fail if regex/config issues)
    service.redis_client = mock_redis_instance
    service.knowledge_base = mock_kb_instance
    
    # Create test document
    doc = Document(
        id=uuid.uuid4(),
        file_name="Summit Concept Note.pdf",
        file_path="/tmp/summit_concept.pdf",
        category="strategic",
        scope=["global"],
        version=1,
        metadata_json={"author": "Secretariat"}
    )
    
    # Execute broadcast
    import asyncio
    asyncio.run(service.broadcast_document(doc, target_agents="ALL"))
    
    # Verify Knowledge Base Upsert
    mock_kb_instance.add_document.assert_called_once()
    args, kwargs = mock_kb_instance.add_document.call_args
    assert kwargs['namespace'] == "global"
    assert kwargs['metadata']['title'] == "Summit Concept Note.pdf"
    assert kwargs['metadata']['category'] == "strategic"
    assert "global" in kwargs['metadata']['scope']
    
    # Verify Redis Notification
    # ALL = 6 agents
    assert mock_redis_instance.lpush.call_count == 6 
    
    # Check one notification content
    call_args = mock_redis_instance.lpush.call_args_list[0]
    queue_name = call_args[0][0]
    payload = json.loads(call_args[0][1])
    
    assert "notifications:" in queue_name
    assert payload['type'] == "new_document"
    assert payload['title'] == "Summit Concept Note.pdf"
    assert payload['action'] == "context_available"

def test_broadcast_document_targeted(mock_redis, mock_kb):
    # Setup mocks
    mock_redis_instance = MagicMock()
    mock_kb_instance = MagicMock()
    
    service = BroadcastService()
    service.redis_client = mock_redis_instance
    service.knowledge_base = mock_kb_instance
    
    doc = Document(
        id=uuid.uuid4(),
        file_name="Technical Specs.pdf",
        scope=["energy_twg"],
        category="twg_specific"
    )
    
    import asyncio
    asyncio.run(service.broadcast_document(doc, target_agents=["energy"]))
    
    # Verify Redis Notification count
    assert mock_redis_instance.lpush.call_count == 1
    assert "notifications:energy" in mock_redis_instance.lpush.call_args[0][0]
