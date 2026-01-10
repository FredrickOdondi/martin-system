"""
API Adapter for LangGraph Supervisor

Provides backward compatibility with the old SupervisorWithTools API
while using the new LangGraph implementation underneath.
"""

from app.agents.langgraph_supervisor import create_langgraph_supervisor
from langgraph.types import interrupt
from langgraph.errors import GraphInterrupt
from loguru import logger


class SupervisorAPIAdapter:
    """
    Adapter to make LangGraph supervisor work with existing API routes.

    Wraps the sync LangGraph supervisor methods to appear async.
    """

    def __init__(self):
        """Initialize the adapter with a LangGraph supervisor."""
        self.supervisor = create_langgraph_supervisor(
            keep_history=True,
            auto_register=True
        )
        logger.info("[ADAPTER] LangGraph supervisor initialized for API")

    async def chat_with_tools(self, message: str, twg_id: str = None) -> str:
        """
        Async wrapper around LangGraph supervisor chat.

        This method is async to maintain compatibility with the API routes,
        but the underlying LangGraph supervisor.chat() is sync.
        
        Raises:
            GraphInterrupt: When the graph requires human approval before continuing.
        """
        try:
            # Call the sync method (LangGraph handles state internally)
            response = self.supervisor.chat(message, twg_id=twg_id)
            return response
        except GraphInterrupt as gi:
            # Re-raise GraphInterrupt so the API can catch it and return the approval payload
            logger.info(f"[ADAPTER] GraphInterrupt detected - propagating to API layer")
            raise gi
        except Exception as e:
            logger.error(f"[ADAPTER] Error in chat_with_tools: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"

    def get_supervisor_status(self):
        """Get supervisor status."""
        return self.supervisor.get_supervisor_status()

    def get_registered_agents(self):
        """Get list of registered agents."""
        return self.supervisor.get_registered_agents()


# For backward compatibility
class SupervisorWithTools(SupervisorAPIAdapter):
    """
    Alias for SupervisorAPIAdapter to maintain backward compatibility.
    """
    pass

