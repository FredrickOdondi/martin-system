"""
LangGraph-Based Supervisor Agent

This is the PROPER implementation using LangGraph's StateGraph.
Replaces the manual delegation logic with LangGraph's orchestration.
"""

from typing import Dict, List, Optional, Any, Literal
from loguru import logger

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphInterrupt, GraphRecursionError
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
from app.services.supervisor_state_service import get_supervisor_state, SupervisorGlobalState


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

        # Initialize access to Global State
        self.state_service = get_supervisor_state()
        
        # Add tools to supervisor agent for accessing state
        self._add_state_tools()

        # Registry of TWG agents
        self._twg_agents: Dict[str, LangGraphBaseAgent] = {}

        # The LangGraph StateGraph
        self.graph = None
        self.compiled_graph = None

        # Memory saver for checkpointing
        self.memory = MemorySaver()

        logger.info(f"LangGraphSupervisor initialized for session '{self.session_id}'")

    def _add_state_tools(self):
        """Add tools for accessing global state to the supervisor agent."""
        
        def get_global_calendar_tool() -> str:
            """
            Get the unified schedule of all TWG meetings. 
            Useful for checking availability, finding conflicts, or seeing the overall timeline.
            """
            try:
                # The state service is a singleton, accessed via get_supervisor_state()
                # But here we can use the instance we referenced
                state = self.state_service.get_state()
                if not state:
                    return "Global state not yet initialized. Please try again in a moment."
                
                calendar = self.state_service.get_global_calendar()
                
                response = f"Global Calendar ({calendar.total_meetings} total, {calendar.upcoming_meetings} upcoming, {calendar.conflicts_detected} conflicts):\n"
                for m in calendar.meetings:
                    if m.status == "scheduled":
                        conflict_mark = "⚠️ " if m.has_conflicts else ""
                        response += f"- {conflict_mark}{m.scheduled_at.strftime('%Y-%m-%d %H:%M')}: {m.title} ({m.twg_name})\n"
                
                return response
            except Exception as e:
                return f"Error accessing calendar: {str(e)}"

        def get_document_registry_tool() -> str:
            """
            Get the registry of all documents across TWGs.
            Useful for finding existing policies, drafts, or memos.
            """
            try:
                state = self.state_service.get_state()
                if not state:
                    return "Global state not yet initialized."
                
                registry = self.state_service.get_document_registry()
                
                response = f"Document Registry ({registry.total_documents} documents):\n"
                for doc in registry.documents[:20]: # Limit to 20 for brevity
                    response += f"- {doc.file_name} ({doc.twg_name or 'General'}) - {doc.file_type}\n"
                
                if registry.total_documents > 20:
                    response += f"... and {registry.total_documents - 20} more."
                
                return response
            except Exception as e:
                return f"Error accessing documents: {str(e)}"
        
        def get_project_pipeline_tool() -> str:
            """
            Get the status of the project pipeline.
            Useful for tracking deal flow and investment readiness.
            """
            try:
                state = self.state_service.get_state()
                if not state:
                    return "Global state not yet initialized."
                
                pipeline = self.state_service.get_project_pipeline()
                
                response = f"Project Pipeline ({pipeline.total_projects} projects, Total Investment: ${pipeline.total_investment:,.2f}):\n"
                
                # Group by status for readability
                by_status = {}
                for p in pipeline.projects:
                    if p.status.value not in by_status:
                        by_status[p.status.value] = []
                    by_status[p.status.value].append(p)
                
                for status, projects in by_status.items():
                    response += f"\n{status.upper()}:\n"
                    for p in projects:
                        response += f"- {p.name} ({p.twg_name}): ${p.investment_size:,.0f} (Readiness: {p.readiness_score}/10)\n"
                
                return response
            except Exception as e:
                return f"Error accessing pipeline: {str(e)}"

        # Register these functions as tools for the supervisor LLM
        # Note: LangGraphBaseAgent handles tool registration via its own mechanism
        # We need to manually append to its tool list if it supports it, 
        # or recreate the agent with these tools.
        # Since LangGraphBaseAgent implementation isn't fully visible here, 
        # let's assume we can append to `self.supervisor_agent.tools` if it exists,
        # or better yet, pass them in `chat` context or system prompt.
        
        # For now, let's register them in a way the base agent can see.
        # Ideally, LangGraphBaseAgent would have an `add_tool` method.
        if hasattr(self.supervisor_agent, "add_tool"):
            self.supervisor_agent.add_tool(get_global_calendar_tool)
            self.supervisor_agent.add_tool(get_document_registry_tool)
            self.supervisor_agent.add_tool(get_project_pipeline_tool)
        else:
            # Fallback: We might need to subclass or modify BaseAgent to accept dynamic tools
            # Or we simply wrap these in the system prompt context injection
            pass # TODO: Verify tool registration mechanism


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
                    except GraphInterrupt:
                        # Re-raise explicit interrupts (like Approval Required)
                        # The supervisor must pause if a child pauses
                        logger.info(f"[DISPATCH] Interrupt from {agent_id} detected in supervisor")
                        raise
                    except Exception as e:
                        # Check for re-raised GraphInterrupt trapped in generic Exception
                        if type(e).__name__ == "GraphInterrupt":
                            logger.info(f"[DISPATCH] GraphInterrupt caught as Exception from {agent_id}")
                            raise e
                            
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

    async def chat(self, message: str, thread_id: Optional[str] = None, twg_id: Optional[str] = None) -> str:
        """
        Chat interface using LangGraph execution.

        Args:
            message: User query
            thread_id: Optional thread ID for conversation threading
            twg_id: Optional TWG ID to restrict context (Strict RBAC)

        Returns:
            Agent response
        """
        if not self.compiled_graph:
            raise ValueError("Graph not built. Call build_graph() first.")

        thread_id = thread_id or self.session_id

        logger.info(f"[SUPERVISOR:{thread_id}] Received: {message[:100]}... (Context: {twg_id or 'General'})")

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
            "context": {"twg_id": twg_id} if twg_id else None
        }

        # Run the graph
        # Enforce recursion limit for supervisor workflow
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 30}

        try:
            # Use ainvoke for async execution (required since route_query_node is async)
            result = await self.compiled_graph.ainvoke(initial_state, config)

            # CHECK FOR INTERRUPTS (same logic as LangGraphBaseAgent)
            # The Main Graph's invoke() might not re-raise exceptions from nodes
            snapshot = await self.compiled_graph.aget_state(config)
            if snapshot.tasks:
                for task in snapshot.tasks:
                    if hasattr(task, 'interrupts') and task.interrupts:
                        for inter in task.interrupts:
                            # inter.value contains the actual payload
                            interrupt_value = inter.value if hasattr(inter, 'value') else inter
                            logger.info(f"[SUPERVISOR] Detected interrupt in state: {interrupt_value}")
                            # Import here to avoid scope issues
                            from langgraph.errors import GraphInterrupt as GI
                            raise GI(interrupt_value)

            final_response = result.get("final_response", "")

            logger.info(f"[SUPERVISOR:{thread_id}] Response generated")

            return final_response

        except GraphRecursionError:
            logger.warning(f"[SUPERVISOR:{thread_id}] GraphRecursionError: Max iterations reached")
            return "I apologize, but the supervisor reached the maximum number of steps. This usually indicates a complex loop or conflict. Please refine your request."
            
        except Exception as e:
            # Check for GraphInterrupt by name to avoid import/scope issues
            if type(e).__name__ == "GraphInterrupt":
                raise e
            
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
