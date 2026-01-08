"""
Agriculture & Food Systems TWG Agent - LangGraph Implementation

Proper LangGraph-based agent for Agriculture & Food Systems TWG.
"""

from app.agents.langgraph_base_agent import LangGraphBaseAgent


class LangGraphAgricultureAgent(LangGraphBaseAgent):
    """LangGraph-based Agriculture & Food Systems TWG Agent"""

    def __init__(self, keep_history: bool = True, session_id: str = None):
        """
        Initialize the Agriculture agent with LangGraph.

        Args:
            keep_history: Whether to maintain conversation history
            session_id: Session identifier for checkpointing
        """
        super().__init__(
            agent_id="agriculture",
            keep_history=keep_history,
            max_history=15,
            session_id=session_id
        )


def create_langgraph_agriculture_agent(keep_history: bool = True, session_id: str = None) -> LangGraphAgricultureAgent:
    """Create and return a LangGraph Agriculture agent instance."""
    return LangGraphAgricultureAgent(keep_history=keep_history, session_id=session_id)
