"""
LangGraph Base Agent - PROPER IMPLEMENTATION

All agents (TWG agents and Supervisor) should inherit from this.
Uses LangGraph StateGraph for proper agent orchestration.
"""

from typing import Annotated, TypedDict, List, Dict, Optional, Sequence
from loguru import logger
from operator import add

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from app.services.groq_llm_service import get_llm_service
from app.agents.prompts import get_prompt
from app.core.knowledge_base import get_knowledge_base
from app.agents.utils import get_twg_id_by_agent_id


# Helper function for message accumulation
def add_messages(left: Sequence[BaseMessage], right: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    """Add messages together for state accumulation."""
    return list(left) + list(right)


# =========================================================================
# STATE SCHEMA FOR INDIVIDUAL AGENTS
# =========================================================================

class AgentConversationState(TypedDict):
    """
    State schema for individual agent conversations.

    Each agent maintains its own conversation state using LangGraph.
    """
    # Messages using custom message handling
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Current query
    query: str

    # Response
    response: str

    # Agent metadata
    agent_id: str
    session_id: str

    # Context (optional)
    context: Optional[Dict]


# =========================================================================
# LANGGRAPH BASE AGENT CLASS
# =========================================================================

class LangGraphBaseAgent:
    """
    Base class for ALL agents using LangGraph StateGraph.

    This replaces the old BaseAgent with proper LangGraph orchestration.
    Every TWG agent and the Supervisor should use this.
    """

    def __init__(
        self,
        agent_id: str,
        keep_history: bool = True,
        max_history: int = 10,
        session_id: Optional[str] = None,
        use_redis: bool = False,
        memory_ttl: Optional[int] = None
    ):
        """
        Initialize a LangGraph-based agent.

        Args:
            agent_id: Unique identifier (e.g., 'energy', 'agriculture', 'supervisor')
            keep_history: Whether to maintain conversation history
            max_history: Maximum messages to keep
            session_id: Session identifier for checkpointing
            use_redis: If True, use Redis checkpointer (future)
            memory_ttl: TTL for memory (optional)
        """
        self.agent_id = agent_id
        self.keep_history = keep_history
        self.max_history = max_history
        self.session_id = session_id or "default"
        self.use_redis = use_redis
        self.memory_ttl = memory_ttl

        # Load system prompt
        try:
            self.system_prompt = get_prompt(agent_id)
            logger.info(f"[{agent_id}] Loaded system prompt")
        except ValueError as e:
            logger.error(f"[{agent_id}] Failed to load prompt: {e}")
            raise

        # Get LLM service
        self.llm = get_llm_service()
        
        # Get Knowledge Base (RAG)
        try:
            self.kb = get_knowledge_base()
        except Exception as e:
            logger.warning(f"[{agent_id}] Knowledge Base not available: {e}")
            self.kb = None
            
        # Resolve TWG ID for RAG context scoping
        from app.agents.utils import get_twg_id_by_agent_id # Import locally to avoid circulars if any
        self.twg_id = get_twg_id_by_agent_id(agent_id)
        if self.twg_id:
            logger.info(f"[{agent_id}] RAG Enabled. Scoped to TWG: {self.twg_id}")

        # LangGraph components
        self.graph = None
        self.compiled_graph = None
        self.memory = MemorySaver()  # In-memory checkpointer

        # Build the agent's graph
        self._build_graph()

        logger.info(f"[{agent_id}] LangGraph agent initialized")

    def _build_graph(self) -> None:
        """
        Build the LangGraph StateGraph for this agent.

        Default implementation: simple query -> process -> respond flow.
        Subclasses can override for more complex workflows.
        """
        workflow = StateGraph(AgentConversationState)

        # Add nodes
        workflow.add_node("process_query", self._process_query_node)
        workflow.add_node("generate_response", self._generate_response_node)

        # Set entry point
        workflow.set_entry_point("process_query")

        # Add edges
        workflow.add_edge("process_query", "generate_response")
        workflow.add_edge("generate_response", END)

        # Compile with checkpointing
        self.graph = workflow
        self.compiled_graph = workflow.compile(checkpointer=self.memory)

        logger.info(f"[{self.agent_id}] StateGraph compiled")

    def _process_query_node(self, state: AgentConversationState) -> AgentConversationState:
        """
        Process the incoming query.

        Default implementation: just passes through.
        Subclasses can override for preprocessing, tool calls, etc.
        """
        logger.debug(f"[{self.agent_id}] Processing query: {state['query'][:100]}...")
        
        # --- RAG RETRIEVAL ---
        if self.twg_id and self.kb:
            try:
                # Search specifically in this TWG's namespace
                namespace = f"twg-{self.twg_id}"
                results = self.kb.search(
                    query=state['query'], 
                    namespace=namespace, 
                    top_k=2 # Reduced from 3 to save tokens
                )
                
                if results:
                    # Format context with strict truncation
                    # Assuming 4 chars per token, 2500 chars is ~625 tokens per doc
                    # Total context ~1250 tokens, leaving plenty of room
                    context_parts = []
                    for r in results:
                        file_name = r['metadata'].get('file_name', 'Unknown')
                        text = r['metadata'].get('text', '') or ''
                        # Truncate text to 2500 chars to avoid 413 errors
                        truncated_text = text[:2500] + "..." if len(text) > 2500 else text
                        context_parts.append(f"[Document: {file_name}]\n{truncated_text}")

                    context_text = "\n\n".join(context_parts)
                    
                    # Store in state
                    state['context'] = {"retrieved_docs": context_text, "source": namespace}
                    logger.info(f"[{self.agent_id}] Retrieved {len(results)} docs from {namespace}")
                else:
                    logger.info(f"[{self.agent_id}] No relevant docs found in {namespace}")
                    
            except Exception as e:
                logger.error(f"[{self.agent_id}] RAG Search failed: {e}")
                
        return state

    def _generate_response_node(self, state: AgentConversationState) -> AgentConversationState:
        """
        Generate response using LLM.

        This is where the actual LLM call happens.
        """
        query = state["query"]
        messages = state.get("messages", [])

        logger.info(f"[{self.agent_id}] Generating response...")

        try:
            if self.keep_history and len(messages) > 1:
                # Use conversation history
                # Convert messages to dict format for our LLM service
                history = []
                for msg in messages:
                    if isinstance(msg, HumanMessage):
                        history.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        history.append({"role": "assistant", "content": msg.content})

                # Inject RAG context into System Prompt for history-aware chat
                sys_prompt = self.system_prompt
                context = state.get("context")
                if context and "retrieved_docs" in context:
                    sys_prompt = f"{self.system_prompt}\n\nRelevant Context from Knowledge Base:\n{context['retrieved_docs']}"
                    logger.debug(f"[{self.agent_id}] Injected RAG context into system prompt")

                response = self.llm.chat_with_history(
                    messages=history,
                    system_prompt=sys_prompt
                )
            else:
                # No history or first message
                # Prepare prompt with RAG context if available
                final_prompt = query
                context = state.get("context")
                if context and "retrieved_docs" in context:
                    final_prompt = f"Background Information (Use this to answer if relevant):\n{context['retrieved_docs']}\n\nUser Question: {query}"
                    logger.info(f"[{self.agent_id}] Injected RAG context into prompt")

                response = self.llm.chat(
                    prompt=final_prompt,
                    system_prompt=self.system_prompt
                )

            state["response"] = response

            # Add AI response to messages
            state["messages"].append(AIMessage(content=response))

            logger.info(f"[{self.agent_id}] Response generated")

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(f"[{self.agent_id}] {error_msg}")
            state["response"] = f"I apologize, but I encountered an error: {str(e)}"
            state["messages"].append(AIMessage(content=state["response"]))

        return state

    def chat(self, message: str, thread_id: Optional[str] = None) -> str:
        """
        Chat interface using LangGraph execution.

        Args:
            message: User message
            thread_id: Optional thread ID for conversation threading

        Returns:
            Agent response
        """
        if not self.compiled_graph:
            raise ValueError(f"[{self.agent_id}] Graph not compiled")

        thread_id = thread_id or self.session_id

        logger.info(f"[{self.agent_id}:{thread_id}] Received: {message[:100]}...")

        # Get existing state from checkpointer if available
        config = {"configurable": {"thread_id": thread_id}}

        # Initialize or update state
        initial_state: AgentConversationState = {
            "messages": [HumanMessage(content=message)],
            "query": message,
            "response": "",
            "agent_id": self.agent_id,
            "session_id": thread_id,
            "context": None
        }

        try:
            # Run the graph
            result = self.compiled_graph.invoke(initial_state, config)

            response = result.get("response", "")

            logger.info(f"[{self.agent_id}:{thread_id}] Response: {response[:100]}...")

            return response

        except Exception as e:
            logger.error(f"[{self.agent_id}:{thread_id}] Error: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"

    def reset_history(self, thread_id: Optional[str] = None):
        """
        Clear conversation history for a thread.

        With LangGraph, you can clear by using a new thread_id.
        """
        thread_id = thread_id or self.session_id
        logger.info(f"[{self.agent_id}:{thread_id}] History cleared (use new thread_id for fresh conversation)")

    def get_agent_info(self) -> Dict:
        """Get agent information."""
        return {
            "agent_id": self.agent_id,
            "agent_type": "LangGraph StateGraph",
            "langgraph_version": "1.0.5+",
            "system_prompt": self.system_prompt[:200] + "...",
            "keep_history": self.keep_history,
            "max_history": self.max_history,
            "session_id": self.session_id,
            "graph_compiled": self.compiled_graph is not None,
            "checkpointing_enabled": True
        }

    def get_graph_visualization(self) -> str:
        """
        Get ASCII visualization of the agent's graph.
        """
        if not self.compiled_graph:
            return "Graph not built"

        try:
            return str(self.compiled_graph.get_graph().draw_ascii())
        except Exception as e:
            logger.warning(f"Could not generate visualization: {e}")
            return "Visualization not available"

    def __repr__(self) -> str:
        return f"<LangGraphAgent: {self.agent_id}>"


# =========================================================================
# FACTORY FUNCTION
# =========================================================================

def create_langgraph_agent(
    agent_id: str,
    keep_history: bool = True,
    session_id: Optional[str] = None
) -> LangGraphBaseAgent:
    """
    Factory function to create a LangGraph-based agent.

    Args:
        agent_id: Agent identifier
        keep_history: Whether to maintain conversation history
        session_id: Session identifier

    Returns:
        Configured LangGraphBaseAgent instance
    """
    return LangGraphBaseAgent(
        agent_id=agent_id,
        keep_history=keep_history,
        session_id=session_id
    )
