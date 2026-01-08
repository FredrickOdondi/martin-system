"""
Resource Mobilization TWG Agent - LangGraph Implementation

Proper LangGraph-based agent for Resource Mobilization TWG.
"""

from app.agents.langgraph_base_agent import LangGraphBaseAgent


class LangGraphResourceMobilizationAgent(LangGraphBaseAgent):
    """LangGraph-based Resource Mobilization TWG Agent"""

    def __init__(self, keep_history: bool = True, session_id: str = None):
        """
        Initialize the Resource Mobilization agent with LangGraph.

        Args:
            keep_history: Whether to maintain conversation history
            session_id: Session identifier for checkpointing
        """
        super().__init__(
            agent_id="resource_mobilization",
            keep_history=keep_history,
            max_history=15,
            session_id=session_id
        )


def create_langgraph_resource_mobilization_agent(keep_history: bool = True, session_id: str = None) -> LangGraphResourceMobilizationAgent:
    """Create and return a LangGraph Resource Mobilization agent instance."""
    return LangGraphResourceMobilizationAgent(keep_history=keep_history, session_id=session_id)
