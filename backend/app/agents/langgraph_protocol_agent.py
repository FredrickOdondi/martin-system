"""
Protocol & Logistics TWG Agent - LangGraph Implementation

Proper LangGraph-based agent for Protocol & Logistics TWG.
"""

from app.agents.langgraph_base_agent import LangGraphBaseAgent


class LangGraphProtocolAgent(LangGraphBaseAgent):
    """LangGraph-based Protocol & Logistics TWG Agent"""

    def __init__(self, keep_history: bool = True, session_id: str = None):
        """
        Initialize the Protocol agent with LangGraph.

        Args:
            keep_history: Whether to maintain conversation history
            session_id: Session identifier for checkpointing
        """
        super().__init__(
            agent_id="protocol",
            keep_history=keep_history,
            max_history=15,
            session_id=session_id
        )


def create_langgraph_protocol_agent(keep_history: bool = True, session_id: str = None) -> LangGraphProtocolAgent:
    """Create and return a LangGraph Protocol agent instance."""
    return LangGraphProtocolAgent(keep_history=keep_history, session_id=session_id)
