"""
Supervisor Agent

Central coordinator and orchestrator for all TWG agents.
Routes requests, synthesizes outputs, and maintains global consistency.
"""

from app.agents.base_agent import BaseAgent


class SupervisorAgent(BaseAgent):
    """Supervisor agent for coordinating all TWG agents"""

    def __init__(self, keep_history: bool = True):
        """
        Initialize the Supervisor agent.

        Args:
            keep_history: Whether to maintain conversation history (default: True)
        """
        super().__init__(
            agent_id="supervisor",
            keep_history=keep_history,
            max_history=20  # Supervisors may need longer context
        )


# Convenience function to create a supervisor agent
def create_supervisor(keep_history: bool = True) -> SupervisorAgent:
    """Create and return a Supervisor agent instance"""
    return SupervisorAgent(keep_history=keep_history)
