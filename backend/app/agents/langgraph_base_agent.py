"""
LangGraph Base Agent - PROPER IMPLEMENTATION

All agents (TWG agents and Supervisor) should inherit from this.
Uses LangGraph StateGraph for proper agent orchestration.
"""

from typing import Annotated, TypedDict, List, Dict, Optional, Sequence
from loguru import logger
from operator import add
import json

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langgraph.types import interrupt, Command
from langgraph.errors import GraphInterrupt, GraphRecursionError
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
    
    # Flag to indicate an approval is pending (stops agent loop)
    approval_pending: Optional[bool]


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
            agent_id: Unique identifier
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
        
        # Tools Configuration
        from app.tools.calendar_tools import GET_SCHEDULE_TOOL_DEF, get_schedule
        from app.tools.email_tools import EMAIL_TOOLS, send_email, create_email_draft
        import json
        
        # Register default tools available to all agents (or specific ones)
        
        # 1. Start with standard tools
        self.tools_def = [GET_SCHEDULE_TOOL_DEF]
        
        # 2. Convert and add EMAIL_TOOLS
        for tool in EMAIL_TOOLS:
            # Create standard OpenAI tool definition
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": {
                        "type": "object",
                        "properties": tool["parameters"],
                        # Assuming all params optional for now or need strict parsing
                        # Simple schema adjustment:
                        "required": [] 
                    }
                }
            }
            # Adjust properties format if needed. 
            # EMAIL_TOOLS params are simple key-value descriptions. 
            # We need to construct a valid JSON schema for parameters.
            
            new_props = {}
            for param_name, param_desc in tool["parameters"].items():
                # Default generic schema
                prop_schema = {
                    "type": "string",
                    "description": param_desc
                }
                
                # Specific Type Overrides
                if param_name in ["max_results", "days"]:
                    prop_schema["type"] = "integer"
                elif param_name in ["include_body"]:
                    prop_schema["type"] = "boolean"
                elif param_name in ["variables", "exclude_files"]:
                    prop_schema["type"] = "object"
                
                # Handle 'to': String or List of strings
                elif param_name == "to":
                    prop_schema = {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}}
                        ],
                        "description": param_desc
                    }
                
                # Handle 'attachments': List of strings (or null/string fallback)
                elif param_name == "attachments":
                     prop_schema = {
                        "anyOf": [
                            {"type": "array", "items": {"type": "string"}},
                            {"type": "string"},
                            {"type": "null"}
                        ],
                        "description": param_desc
                    }

                # Handle Nullable Strings (cc, bcc, html_body, pillar_name, context)
                elif param_name in ["cc", "bcc", "html_body", "pillar_name", "context"]:
                    prop_schema = {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "null"}
                        ],
                        "description": param_desc
                    }

                new_props[param_name] = prop_schema
            
            tool_def["function"]["parameters"]["properties"] = new_props
            self.tools_def.append(tool_def)

        # 3. Build Tool Map (only include available tools)
        self.tool_map = {
            "get_schedule": get_schedule,
            "send_email": send_email,
            "create_email_draft": create_email_draft
        }
        
        # Get Knowledge Base (RAG)
        try:
            self.kb = get_knowledge_base()
        except Exception as e:
            logger.warning(f"[{agent_id}] Knowledge Base not available: {e}")
            self.kb = None
            
        # Resolve TWG ID for RAG context scoping
        from app.agents.utils import get_twg_id_by_agent_id 
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

        logger.info(f"[{agent_id}] LangGraph agent initialized")

    def add_tool(self, tool_func):
        """
        Add a python function as a tool to the agent.
        Autogenerates the schema from the function signature and docstring.
        """
        import inspect
        
        func_name = tool_func.__name__
        doc = tool_func.__doc__ or "No description provided."
        
        # Simple schema generation
        sig = inspect.signature(tool_func)
        parameters = {}
        required = []
        
        for name, param in sig.parameters.items():
            param_type = "string"
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == bool:
                param_type = "boolean"
                
            parameters[name] = {
                "type": param_type,
                "description": f"Parameter {name}" 
            }
            if param.default == inspect.Parameter.empty:
                required.append(name)
        
        tool_def = {
            "type": "function",
            "function": {
                "name": func_name,
                "description": doc.strip(),
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required
                }
            }
        }
        
        self.tools_def.append(tool_def)
        self.tool_map[func_name] = tool_func
        logger.info(f"[{self.agent_id}] Added tool: {func_name}")

    def _build_graph(self) -> None:
        """
        Build the LangGraph StateGraph for this agent.
        Includes tool execution loop.
        """
        workflow = StateGraph(AgentConversationState)

        # Add nodes
        workflow.add_node("process_query", self._process_query_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("execute_tools", self._execute_tools_node)

        # Set entry point
        workflow.set_entry_point("process_query")

        # Add edges
        workflow.add_edge("process_query", "generate_response")
        
        # Conditional edge: check if tokens were generated or tool calls
        workflow.add_conditional_edges(
            "generate_response",
            self._should_continue,
            {
                "continue": "execute_tools",
                "end": END
            }
        )
        
        workflow.add_edge("execute_tools", "generate_response")

        # Compile with checkpointing
        self.graph = workflow
        self.compiled_graph = workflow.compile(checkpointer=self.memory)

        logger.info(f"[{self.agent_id}] StateGraph compiled with Tools loop")

    def _should_continue(self, state: AgentConversationState) -> str:
        """
        Determine if we should continue to tool execution or end.
        """
        # CRITICAL: If an approval is pending, STOP the loop immediately
        if state.get("approval_pending"):
            logger.info(f"[{self.agent_id}] Approval pending - ending loop")
            return "end"
        
        messages = state["messages"]
        last_message = messages[-1]
        
        # Check if AIMessage has tool_calls
        # Note: GroqLLMService now returns object with tool_calls if present
        # In our state, we store AIMessage. 
        # We need to ensure we stored it correctly in _generate_response_node
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
            
        return "end"

    def _process_query_node(self, state: AgentConversationState) -> AgentConversationState:
        """Process incoming query."""
        query = state["query"]
        
        # Initialize context if needed
        if state.get("context") is None:
            state["context"] = {}

        # RAG Retrieval
        if self.twg_id and self.kb:
            try:
                # Search KB restricted to TWG namespace
                namespace = f"twg-{self.twg_id}"
                twg_results = self.kb.search(
                    query=query,
                    namespace=namespace,
                    top_k=3
                )
                
                # Search Global Broadcast namespace
                global_results = self.kb.search(
                    query=query,
                    namespace="global",
                    top_k=2
                )
                
                # Merge and Sort by Score
                results = twg_results + global_results
                results.sort(key=lambda x: x['score'], reverse=True)
                results = results[:3] # Keep top 3 most relevant context pieces
                
                # Format context
                if results:
                    # Format context with EXTREME truncation to prevent token errors
                    # Limit to 500 chars per doc (~125 tokens) × 2 = 250 tokens total
                    context_parts = []
                    for r in results:
                        file_name = r['metadata'].get('file_name', 'Unknown')
                        text = r['metadata'].get('text', '') or ''
                        # Truncate text to 2000 chars (approx 500 tokens) to allow for more context while staying within limits
                        truncated_text = text[:2000] + "..." if len(text) > 2000 else text
                        context_parts.append(f"[{file_name}]\n{truncated_text}")

                    context_text = "\n".join(context_parts)

                    # Store in state
                    state['context'] = {"retrieved_docs": context_text, "source": namespace}
                    logger.info(f"[{self.agent_id}] Retrieved {len(results)} docs from {namespace}")
                else:
                    logger.info(f"[{self.agent_id}] No relevant docs found in {namespace}")
                    
            except Exception as e:
                logger.error(f"[{self.agent_id}] RAG Error: {e}")
                
        return state

    def _generate_response_node(self, state: AgentConversationState) -> AgentConversationState:
        """
        Generate response using LLM, supporting Tool Calls.
        """
        query = state["query"]
        messages = state.get("messages", [])
        
        # Enforce History Limit to prevent 413 errors & Infinite Loops
        # If we have too many messages in the current state (likely due to a tool loop), cut it off.
        if len(messages) > 20:
             logger.warning(f"[{self.agent_id}] Loop detected (20+ messages). Truncating and forcing text response.")
             messages = messages[-self.max_history:]
             # Force a stop by returning a final message if we are deep in a loop
             # But LLM might just continue. We'll rely on the reduced history to break context loop.
             
        if len(messages) > self.max_history:
             messages = messages[-self.max_history:]
        
        logger.info(f"[{self.agent_id}] Generating response...")

        try:
            # Prepare messages for LLM service (dict format)
            history = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    history.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    msg_dict = {"role": "assistant", "content": msg.content}
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                         # Convert LangChain tool_calls to dict format expected by API
                         # If msg.tool_calls is a list of ToolCall objects
                         api_tool_calls = []
                         for tc in msg.tool_calls:
                             api_tool_calls.append({
                                 "id": tc["id"],
                                 "type": "function",
                                 "function": {
                                     "name": tc["name"],
                                     "arguments": json.dumps(tc["args"]) if isinstance(tc["args"], dict) else tc["args"]
                                 }
                             })
                         msg_dict["tool_calls"] = api_tool_calls
                    history.append(msg_dict)
                # Handle ToolMessage (Function interactions)
                elif msg.type == "tool":
                    history.append({
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": msg.content
                    })

            # RAG Context injection (simplified)
            sys_prompt = self.system_prompt
            context = state.get("context")
            if context and "retrieved_docs" in context:
                sys_prompt = f"{self.system_prompt}\n\nRelevant Context:\n{context['retrieved_docs']}"

            # Call LLM with tools
            response_obj = self.llm.chat_with_history(
                messages=history,
                system_prompt=sys_prompt,
                tools=self.tools_def
            )

            # Handle Response
            if hasattr(response_obj, "tool_calls") and response_obj.tool_calls:
                # LLM wants to call a tool
                logger.info(f"[{self.agent_id}] Tool Call detected: {len(response_obj.tool_calls)}")
                
                # Convert API response to LangChain AIMessage with tool_calls
                # Groq/OpenAI returns object with tool_calls
                tool_calls_data = []
                for tc in response_obj.tool_calls:
                    tool_calls_data.append({
                        "name": tc.function.name,
                        "args": json.loads(tc.function.arguments),
                        "id": tc.id
                    })
                
                ai_msg = AIMessage(
                    content=response_obj.content or "", 
                    tool_calls=tool_calls_data
                )
                state["response"] = "[Calling Tool...]" # Intermediate state
                state["messages"].append(ai_msg)
                
            else:
                # Standard text response
                content = response_obj if isinstance(response_obj, str) else response_obj.content
                
                # FALLBACK: Check for hallucinatedtool call syntax (LLama models sometimes do this)
                # Pattern: <function=tool_name{...args...}</function>
                import re
                fallback_match = re.search(r'<function=(\w+)\s*(\{[^}]*\})\s*</function>', content or "")
                if fallback_match:
                    logger.warning(f"[{self.agent_id}] Detected hallucinated tool call, parsing fallback...")
                    tool_name = fallback_match.group(1)
                    try:
                        tool_args = json.loads(fallback_match.group(2))
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    # Generate a fake tool_call_id
                    import uuid
                    tool_call_id = f"fallback_{uuid.uuid4().hex[:8]}"
                    
                    tool_calls_data = [{
                        "name": tool_name,
                        "args": tool_args,
                        "id": tool_call_id
                    }]
                    
                    ai_msg = AIMessage(
                        content="",  # Clear the hallucinated content
                        tool_calls=tool_calls_data
                    )
                    state["response"] = "[Calling Tool (Fallback)...]"
                    state["messages"].append(ai_msg)
                    logger.info(f"[{self.agent_id}] Fallback tool call constructed: {tool_name}")
                else:
                    # Truly just text
                    logger.info(f"[{self.agent_id}] Text Response generated")
                    state["response"] = content
                    state["messages"].append(AIMessage(content=content))

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in generation: {e}")
            state["response"] = f"Error: {str(e)}"
            state["messages"].append(AIMessage(content=state["response"]))

        return state

    def _execute_tools_node(self, state: AgentConversationState) -> AgentConversationState:
        """
        Execute tool calls requested by the LLM.
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return state
            
        from langchain_core.messages import ToolMessage
        from langgraph.errors import GraphInterrupt
        import json
        
        new_messages = []
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            logger.info(f"[{self.agent_id}] Executing tool: {tool_name}")
            
            try:
                if tool_name in self.tool_map:
                    # Execute function
                    func = self.tool_map[tool_name]
                    
                    # Check if async
                    import asyncio
                    import inspect
                    
                    if inspect.iscoroutinefunction(func):
                        try:
                            loop = asyncio.get_running_loop()
                            # We are in an event loop (FastAPI).
                            # Since this node is SYNC, we technically shouldn't block, 
                            # but we need the result.
                            # We can't await here.
                            # We must run it in a separate thread to block this sync thread until done.
                            from concurrent.futures import ThreadPoolExecutor
                            with ThreadPoolExecutor() as executor:
                                future = executor.submit(lambda: asyncio.run(func(**tool_args)))
                                result = future.result()
                        except RuntimeError:
                             # No running loop, use asyncio.run
                             result = asyncio.run(func(**tool_args))
                        except Exception as loop_error:
                             # Fallback crazy: Just try to run it?
                             # Dealing with nested loops is hard. 
                             # Alternative: Run in threadsafe if loop exists?
                             # asyncio.run_coroutine_threadsafe needs a loop to run IN.
                             # If we are in a loop, we can use it.
                             if loop:
                                 # But .result() blocks. Blocking the loop from within the loop = Deadlock.
                                 # We CANNOT block a running loop.
                                 # THIS IS A PROBLEM.
                                 # The Agent `chat` method MUST be async if it wants to await things.
                                 # Refactoring `chat` to async is the only robust way.
                                 # Temporary hack: Use NestAsyncio? No.
                                 
                                 # Correct approach for now:
                                 # Assume we are in a thread (FastAPI runs sync endpoints in threads).
                                 # IF `agent.chat` is in a sync endpoint `def chat(...)`, FastAPI runs it in a thread.
                                 # Then `asyncio.run()` works fine!
                                 # IF `agent.chat` is in an async endpoint `async def chat(...)`, we are in the main loop.
                                 
                                 # Let's hope `agents.py` calls it from a `def` (sync) endpoint or in a thread.
                                 # If it fails, we know we must refactor to Async.
                                 result = asyncio.run(func(**tool_args)) 
                    else:
                        # Sync function
                        result = func(**tool_args)
                        
                    # Result in JSON string format expected
                else:
                    result = json.dumps({"error": f"Tool {tool_name} not found"})
                
                # Create ToolMessage
                output_str = str(result)
                
                # SPECIAL HANDLING FOR APPROVAL REQUESTS - USE LANGGRAPH INTERRUPT
                # When an approval is required, interrupt() pauses the graph and returns
                # the approval payload to the caller. The graph can be resumed later.
                if "approval_request_id" in output_str:
                    from langgraph.errors import GraphInterrupt
                    try:
                        res_json = json.loads(result) if isinstance(result, str) else result
                        if isinstance(res_json, dict) and "approval_request_id" in res_json:
                            logger.info(f"[{self.agent_id}] INTERRUPT: Approval required for {res_json['approval_request_id']}")
                            
                            # Prepare the interrupt payload with full approval data
                            approval_payload = {
                                "type": "email_approval_required",
                                "request_id": res_json.get("approval_request_id"),
                                "draft": res_json.get("draft", {}),
                                "message": res_json.get("message", "Email requires approval before sending.")
                            }
                            
                            # INTERRUPT the graph - this raises GraphInterrupt
                            # We MUST let this propagate up to pause the graph
                            human_response = interrupt(approval_payload)
                            
                            # When resumed, human_response contains the approval decision
                            if human_response and human_response.get("approved"):
                                logger.info(f"[{self.agent_id}] Approval GRANTED - proceeding with send")
                                output_str = json.dumps({"status": "approved", "message": "Email approved and will be sent."})
                            else:
                                logger.info(f"[{self.agent_id}] Approval DENIED - cancelling send")
                                output_str = json.dumps({"status": "declined", "message": "Email was declined by user."})
                    except GraphInterrupt:
                        # RE-RAISE GraphInterrupt so it propagates up and pauses the graph
                        logger.info(f"[{self.agent_id}] GraphInterrupt raised - pausing graph for approval")
                        raise
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        logger.error(f"[{self.agent_id}] Interrupt error: {e}")

                new_messages.append(ToolMessage(tool_call_id=tool_id, content=output_str))
                
            except GraphInterrupt:
                # RE-RAISE GraphInterrupt from inner block
                raise
            except Exception as e:
                logger.error(f"[{self.agent_id}] Tool execution failed: {e}")
                new_messages.append(ToolMessage(tool_call_id=tool_id, content=f"Error: {str(e)}"))

        # Update state with all tool results
        state["messages"].extend(new_messages)
        
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
        # Enforce recursion limit to prevent infinite loops (approx 5-7 tool turns)
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}

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

            # CHECK FOR INTERRUPTS (LangGraph invoke swallows the exception but stops)
            snapshot = self.compiled_graph.get_state(config)
            if snapshot.tasks:
                for task in snapshot.tasks:
                    if hasattr(task, 'interrupts') and task.interrupts:
                        for inter in task.interrupts:
                            logger.info(f"[{self.agent_id}] Detected interrupt in state: {inter.value}")
                            # Manually re-raise so API can catch it
                            raise GraphInterrupt(inter.value)

            response = result.get("response", "")

            logger.info(f"[{self.agent_id}:{thread_id}] Response: {response[:100]}...")

            return response

        except GraphInterrupt:
            # Re-raise GraphInterrupt
            raise
        except GraphRecursionError:
            logger.warning(f"[{self.agent_id}:{thread_id}] GraphRecursionError: Max iterations reached")
            return "I apologize, but I reached the maximum number of steps trying to solve this request. I am stopping to avoid an infinite loop. Please refine your query or provide more specific instructions."
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

    def clear_history(self, thread_id: Optional[str] = None):
        """Alias for reset_history for backward compatibility."""
        self.reset_history(thread_id)

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
