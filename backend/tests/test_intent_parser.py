import pytest
from app.agents.intent_parser import IntentParser, DirectiveIntent
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_parse_directive_simple():
    # Mock LLM service
    parser = IntentParser()
    parser.llm = MagicMock()
    
    # Mock response with tool call
    mock_message = MagicMock()
    mock_message.tool_calls = [
        MagicMock(
            function=MagicMock(
                arguments='{"primary_action": "draft", "target_twgs": ["energy"], "task_type": "policy", "urgency": "high"}'
            )
        )
    ]
    parser.llm.chat.return_value = mock_message
    
    intent = await parser.parse_directive("Energy TWG needs to draft a policy urgently")
    
    assert intent.primary_action == "draft"
    assert "energy" in intent.target_twgs
    assert intent.urgency == "high"

@pytest.mark.asyncio
async def test_parse_directive_multi_twg():
    parser = IntentParser()
    parser.llm = MagicMock()
    
    mock_message = MagicMock()
    mock_message.tool_calls = [
        MagicMock(
            function=MagicMock(
                arguments='{"primary_action": "schedule", "target_twgs": ["minerals", "digital"], "task_type": "meeting", "urgency": "medium"}'
            )
        )
    ]
    parser.llm.chat.return_value = mock_message
    
    intent = await parser.parse_directive("Schedule a meeting between Minerals and Digital")
    
    assert intent.primary_action == "schedule"
    assert "minerals" in intent.target_twgs
    assert "digital" in intent.target_twgs
