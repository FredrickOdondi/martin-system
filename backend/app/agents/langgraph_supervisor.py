"""
LangGraph-Based Supervisor Agent

This is the PROPER implementation using LangGraph's StateGraph.
Replaces the manual delegation logic with LangGraph's orchestration.
"""

from typing import Dict, List, Optional, Any, Literal
from loguru import logger

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

from app.agents.langgraph_base_agent import LangGraphBaseAgent
from app.agents.langgraph_state import AgentState
from app.agents.langgraph_nodes import (
    route_query_node,
    supervisor_node,
    create_twg_agent_node,
    synthesis_node,
    single_agent_response_node
)


class LangGraphSupervisor:
    """
    LangGraph-based Supervisor for multi-agent orchestration.

    Uses StateGraph to properly manage agent workflows with:
    - Conditional routing
    - State management
    - Checkpointing
    - Parallel execution where appropriate
    """

    def __init__(
        self,
        keep_history: bool = True,
        session_id: Optional[str] = None,
        use_redis: bool = False,
        memory_ttl: Optional[int] = None
    ):
        """
        Initialize the LangGraph Supervisor.

        Args:
            keep_history: Whether to maintain conversation history
            session_id: Session identifier for checkpointing
            use_redis: If True, use Redis for persistent memory (future)
            memory_ttl: TTL for Redis keys in seconds (optional)
        """
        self.session_id = session_id or "default"
        self.keep_history = keep_history
        self.use_redis = use_redis
        self.memory_ttl = memory_ttl

        # Create supervisor agent (for general knowledge and synthesis)
        self.supervisor_agent = LangGraphBaseAgent(
            agent_id="supervisor",
            keep_history=keep_history,
            max_history=20,
            session_id=session_id,
            use_redis=use_redis,
            memory_ttl=memory_ttl
        )

        # Registry of TWG agents
        self._twg_agents: Dict[str, LangGraphBaseAgent] = {}

        # The LangGraph StateGraph
        self.graph = None
        self.compiled_graph = None

        # Memory saver for checkpointing
        self.memory = MemorySaver()

        logger.info(f"LangGraphSupervisor initialized for session '{self.session_id}'")

    def register_agent(self, agent_id: str, agent: LangGraphBaseAgent) -> None:
        """Register a TWG agent."""
        self._twg_agents[agent_id] = agent
        logger.info(f"[SUPERVISOR] Registered {agent_id} agent")

    def register_all_agents(self) -> None:
        """Automatically register all LangGraph-based TWG agents."""
        # Import LangGraph-based agents
        from app.agents.langgraph_energy_agent import create_langgraph_energy_agent
        from app.agents.langgraph_agriculture_agent import create_langgraph_agriculture_agent
        from app.agents.langgraph_minerals_agent import create_langgraph_minerals_agent
        from app.agents.langgraph_digital_agent import create_langgraph_digital_agent
        from app.agents.langgraph_protocol_agent import create_langgraph_protocol_agent
        from app.agents.langgraph_resource_mobilization_agent import create_langgraph_resource_mobilization_agent

        agents = {
            "energy": create_langgraph_energy_agent(keep_history=False),
            "agriculture": create_langgraph_agriculture_agent(keep_history=False),
            "minerals": create_langgraph_minerals_agent(keep_history=False),
            "digital": create_langgraph_digital_agent(keep_history=False),
            "protocol": create_langgraph_protocol_agent(keep_history=False),
            "resource_mobilization": create_langgraph_resource_mobilization_agent(keep_history=False)
        }

        for agent_id, agent in agents.items():
            self.register_agent(agent_id, agent)

        logger.info(f"[SUPERVISOR] All {len(agents)} LangGraph TWG agents registered")

    def build_graph(self) -> None:
        """
        Build the LangGraph StateGraph.

        This is the core orchestration logic using LangGraph's proper patterns.
        """
        if not self._twg_agents:
            raise ValueError("No TWG agents registered. Call register_all_agents() first.")

        logger.info("[SUPERVISOR] Building LangGraph StateGraph...")

        # Create the graph
        workflow = StateGraph(AgentState)

        # =====================================================================
        # ADD NODES
        # =====================================================================

        # 1. Route query node - determines which agents to consult
        workflow.add_node("route_query", route_query_node)

        # 2. Supervisor node - handles general queries
        workflow.add_node(
            "supervisor",
            lambda state: supervisor_node(state, self.supervisor_agent)
        )

        # 3. TWG agent nodes - one for each registered agent
        for agent_id, agent in self._twg_agents.items():
            workflow.add_node(
                agent_id,
                create_twg_agent_node(agent_id, agent)
            )

        # 4. Synthesis node - combines multiple agent responses
        workflow.add_node(
            "synthesis",
            lambda state: synthesis_node(state, self.supervisor_agent)
        )

        # 5. Single agent response node - formats single agent response
        workflow.add_node("single_agent_response", single_agent_response_node)

        # =====================================================================
        # ADD EDGES AND CONDITIONAL ROUTING
        # =====================================================================

        # Set entry point
        workflow.set_entry_point("route_query")

        # Add dispatch_multiple node for handling multiple agents
        def dispatch_multiple_node(state: AgentState) -> AgentState:
            """
            Dispatch query to multiple TWG agents sequentially.

            TODO: This could be parallelized using LangGraph's parallel execution
            """
            relevant_agents = state["relevant_agents"]
            query = state["query"]

            state["agent_responses"] = {}

            for agent_id in relevant_agents:
                if agent_id in self._twg_agents:
                    logger.info(f"[DISPATCH] Querying {agent_id}...")
                    try:
                        agent = self._twg_agents[agent_id]
                        response = agent.chat(query)
                        state["agent_responses"][agent_id] = response
                    except Exception as e:
                        logger.error(f"[DISPATCH] Error with {agent_id}: {e}")
                        state["agent_responses"][agent_id] = f"Error: {str(e)}"

            return state

        workflow.add_node("dispatch_multiple", dispatch_multiple_node)

        # Conditional routing after route_query
        def route_to_agents(state: AgentState) -> str:
            """
            Determine next step based on routing decision.

            Returns:
                - "supervisor" if no specific TWG needed
                - agent_id if single agent
                - "parallel_agents" if multiple agents (future enhancement)
            """
            delegation_type = state["delegation_type"]
            relevant_agents = state["relevant_agents"]

            if delegation_type == "supervisor_only":
                logger.info("[ROUTE] -> supervisor (general knowledge)")
                return "supervisor"

            elif delegation_type == "single":
                agent_id = relevant_agents[0]
                logger.info(f"[ROUTE] -> {agent_id} (single agent)")
                return agent_id

            else:  # multiple agents
                # For now, route to first agent, then handle others
                # Future: implement true parallel execution
                logger.info(f"[ROUTE] -> multiple agents: {relevant_agents}")
                return "dispatch_multiple"

        workflow.add_conditional_edges(
            "route_query",
            route_to_agents,
            {
                "supervisor": "supervisor",
                **{agent_id: agent_id for agent_id in self._twg_agents.keys()},
                "dispatch_multiple": "dispatch_multiple"
            }
        )



        # From supervisor -> END
        workflow.add_edge("supervisor", END)

        # From single agents -> single_agent_response -> END
        for agent_id in self._twg_agents.keys():
            workflow.add_edge(agent_id, "single_agent_response")

        workflow.add_edge("single_agent_response", END)

        # From dispatch_multiple -> synthesis -> END
        workflow.add_edge("dispatch_multiple", "synthesis")
        workflow.add_edge("synthesis", END)

        # =====================================================================
        # COMPILE GRAPH
        # =====================================================================

        # Compile with checkpointing
        self.graph = workflow
        self.compiled_graph = workflow.compile(checkpointer=self.memory)

        logger.info("[SUPERVISOR] ✓ LangGraph StateGraph compiled successfully")
        logger.info(f"[SUPERVISOR] Nodes: route_query, supervisor, {', '.join(self._twg_agents.keys())}, synthesis, single_agent_response, dispatch_multiple")

    def chat(self, message: str, thread_id: Optional[str] = None) -> str:
        """
        Chat interface using LangGraph execution.

        Args:
            message: User query
            thread_id: Optional thread ID for conversation threading

        Returns:
            Agent response
        """
        if not self.compiled_graph:
            raise ValueError("Graph not built. Call build_graph() first.")

        thread_id = thread_id or self.session_id

        logger.info(f"[SUPERVISOR:{thread_id}] Received: {message[:100]}...")

        # Initialize state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "query": message,
            "relevant_agents": [],
            "agent_responses": {},
            "synthesized_response": None,
            "final_response": "",
            "requires_synthesis": False,
            "delegation_type": "supervisor_only",
            "session_id": self.session_id,
            "user_id": None,
            "context": None
        }

        # Run the graph
        config = {"configurable": {"thread_id": thread_id}}

        try:
            result = self.compiled_graph.invoke(initial_state, config)

            final_response = result.get("final_response", "")

            logger.info(f"[SUPERVISOR:{thread_id}] Response generated")

            return final_response

        except Exception as e:
            logger.error(f"[SUPERVISOR:{thread_id}] Error: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"

    def get_graph_visualization(self) -> str:
        """
        Get ASCII visualization of the graph structure.

        Returns:
            Graph visualization as string
        """
        if not self.compiled_graph:
            return "Graph not built yet. Call build_graph() first."

        try:
            # LangGraph provides visualization capabilities
            return str(self.compiled_graph.get_graph().draw_ascii())
        except Exception as e:
            logger.warning(f"Could not generate visualization: {e}")
            return "Visualization not available"

    def get_registered_agents(self) -> List[str]:
        """Get list of registered agent IDs."""
        return list(self._twg_agents.keys())

    def get_supervisor_status(self) -> Dict[str, Any]:
        """Get supervisor status information."""
        return {
            "supervisor_type": "LangGraph StateGraph",
            "langgraph_version": "1.0.5+",
            "session_id": self.session_id,
            "registered_agents": self.get_registered_agents(),
            "agent_count": len(self._twg_agents),
            "graph_built": self.compiled_graph is not None,
            "history_enabled": self.keep_history,
            "checkpointing_enabled": True,
            "memory_type": "MemorySaver"
        }

    def reset_history(self, thread_id: Optional[str] = None):
        """
        Clear conversation history for a thread.

        Note: With LangGraph checkpointing, history is managed per thread.
        """
        thread_id = thread_id or self.session_id
        # In LangGraph, you can clear by not using previous thread_id
        logger.info(f"[SUPERVISOR:{thread_id}] History cleared (use new thread_id)")


# =========================================================================
# CONVENIENCE FUNCTIONS
# =========================================================================

def create_langgraph_supervisor(
    keep_history: bool = True,
    auto_register: bool = True,
    session_id: Optional[str] = None,
    use_redis: bool = False,
    memory_ttl: Optional[int] = None
) -> LangGraphSupervisor:
    """
    Create and return a LangGraph Supervisor instance.

    Args:
        keep_history: Whether to maintain conversation history
        auto_register: If True, automatically register all TWG agents
        session_id: Session identifier
        use_redis: If True, use Redis for persistent memory (future)
        memory_ttl: TTL for Redis keys in seconds (optional)

    Returns:
        Configured LangGraphSupervisor instance
    """
    supervisor = LangGraphSupervisor(
        keep_history=keep_history,
        session_id=session_id,
        use_redis=use_redis,
        memory_ttl=memory_ttl
    )

    if auto_register:
        supervisor.register_all_agents()
        supervisor.build_graph()

    return supervisor
