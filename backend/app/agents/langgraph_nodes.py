"""
LangGraph Node Functions for Multi-Agent System

Each function represents a node in the agent graph.
"""

from typing import Dict, List
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.errors import GraphInterrupt

from app.agents.langgraph_state import AgentState
from app.agents.langgraph_base_agent import LangGraphBaseAgent


# =========================================================================
# ROUTING NODE - Determines which agents should handle the query
# =========================================================================

def route_query_node(state: AgentState) -> AgentState:
    """
    Analyze the query and determine which TWG agents are relevant.

    This is the routing logic that was previously in SupervisorAgent.identify_relevant_agents()
    """
    query = state["query"]
    query_lower = query.lower()
    
    # --- STRICT RBAC ENFORCEMENT ---
    context = state.get("context")
    if context and context.get("twg_id"):
        twg_id = context.get("twg_id")
        from app.agents.utils import get_agent_id_by_twg_id
        forced_agent_id = get_agent_id_by_twg_id(twg_id)
        
        if forced_agent_id:
            logger.info(f"[ROUTE] Strict RBAC: Context restricted to {forced_agent_id.upper()}")
            # Force routing to single agent
            state["relevant_agents"] = [forced_agent_id]
            state["delegation_type"] = "single"
            state["requires_synthesis"] = False
            return state
        else:
            logger.warning(f"[ROUTE] Context twg_id {twg_id} did not resolve to an agent. STRICT RBAC BLOCKING.")
            # Fail Closed: Do not allow fallback to Supervisor
            state["relevant_agents"] = []
            state["delegation_type"] = "rbac_failure" 
            return state
    
    # Keyword-based routing (Standard)
    agent_domains = {
        "energy": {
            "primary": ["energy", "infrastructure", "power", "electricity", "renewable", "solar", "wind", "wapp"],
            "secondary": ["grid", "transmission", "hydroelectric", "fuel", "petroleum"]
        },
        "agriculture": {
            "primary": ["agriculture", "food system", "food security", "farming", "crop", "livestock", "agribusiness"],
            "secondary": ["fertilizer", "irrigation", "harvest", "rural", "farmer", "food production"]
        },
        "minerals": {
            "primary": ["mining", "mineral", "critical minerals", "industrialization", "cobalt", "lithium", "gold", "bauxite", "extraction"],
            "secondary": ["value chain", "ore", "quarry", "geology"]
        },
        "digital": {
            "primary": ["digital", "technology", "internet", "broadband", "fintech", "e-commerce", "e-government", "transformation"],
            "secondary": ["cybersecurity", "ai", "software", "tech", "online", "platform"]
        },
        "protocol": {
            "primary": ["meeting", "schedule", "logistics", "protocol", "venue", "registration", "invitation"],
            "secondary": ["deadline", "agenda", "ceremony", "security", "vip"]
        },
        "resource_mobilization": {
            "primary": ["investment", "financing", "deal room", "funding", "investor", "bankable", "resource mobilization"],
            "secondary": ["finance", "capital", "donor", "partner", "budget"]
        }
    }

    agent_scores = {}

    # Score each agent based on keyword matches
    for agent_id, keywords in agent_domains.items():
        score = 0

        # Check primary keywords (10 points each)
        for keyword in keywords.get("primary", []):
            if keyword in query_lower:
                score += 10
                logger.debug(f"Primary match '{keyword}' for {agent_id} (+10)")

        # Check secondary keywords (3 points each)
        for keyword in keywords.get("secondary", []):
            if keyword in query_lower:
                score += 3
                logger.debug(f"Secondary match '{keyword}' for {agent_id} (+3)")

        if score > 0:
            agent_scores[agent_id] = score

    # Filter agents that meet threshold (5 points minimum)
    relevant_threshold = 5
    relevant = [
        agent_id for agent_id, score in agent_scores.items()
        if score >= relevant_threshold
    ]

    # Sort by score (highest first)
    relevant.sort(key=lambda x: agent_scores[x], reverse=True)

    if relevant:
        scores_str = ", ".join([f"{a}({agent_scores[a]})" for a in relevant])
        logger.info(f"[ROUTE] Relevant agents identified: {scores_str}")
    else:
        logger.info(f"[ROUTE] No specific TWG identified, will use supervisor")

    # Determine delegation type
    if not relevant:
        delegation_type = "supervisor_only"
    elif len(relevant) == 1:
        delegation_type = "single"
    else:
        delegation_type = "multiple"

    state["relevant_agents"] = relevant
    state["delegation_type"] = delegation_type
    state["requires_synthesis"] = len(relevant) > 1

    return state


# =========================================================================
# SUPERVISOR NODE - Handles general queries without specific TWG
# =========================================================================

def supervisor_node(state: AgentState, supervisor_agent: LangGraphBaseAgent) -> AgentState:
    """
    Handle queries that don't require specific TWG expertise.
    Uses the supervisor's general knowledge.
    """
    query = state["query"]
    logger.info(f"[SUPERVISOR] Handling query with general knowledge")

    response = supervisor_agent.chat(query)

    state["final_response"] = response
    state["agent_responses"]["supervisor"] = response

    return state


# =========================================================================
# TWG AGENT NODES - Delegate to specific TWG agents
# =========================================================================

def create_twg_agent_node(agent_id: str, agent: LangGraphBaseAgent):
    """
    Factory function to create a TWG agent node.

    Returns a function that can be used as a LangGraph node.
    """
    # Use default args to capture values at definition time, not call time
    def twg_node(state: AgentState, _agent_id: str = agent_id, _agent: LangGraphBaseAgent = agent) -> AgentState:
        """
        Delegate query to a specific TWG agent.
        """
        query = state["query"]
        logger.info(f"[{_agent_id.upper()}] Processing query")

        try:
            response = _agent.chat(query)
            state["agent_responses"][_agent_id] = response
            logger.info(f"[{_agent_id.upper()}] Response generated")
        except GraphInterrupt:
            # Re-raise GraphInterrupt so it bubbles up to Supervisor and API
            raise
        except Exception as e:
            logger.error(f"[{_agent_id.upper()}] Error: {e}")
            state["agent_responses"][_agent_id] = f"Error: {str(e)}"

        return state

    return twg_node


# =========================================================================
# SYNTHESIS NODE - Combine responses from multiple agents
# =========================================================================

def synthesis_node(state: AgentState, supervisor_agent: LangGraphBaseAgent) -> AgentState:
    """
    Synthesize responses from multiple TWG agents into a coherent answer.
    """
    query = state["query"]
    responses = state["agent_responses"]

    if not responses:
        state["final_response"] = "I couldn't get responses from the relevant agents."
        return state

    logger.info(f"[SYNTHESIS] Combining {len(responses)} agent responses")

    # Build header showing which agents were consulted
    agent_list = ", ".join([agent_id.upper() for agent_id in responses.keys()])
    output = f"[Consulted {len(responses)} TWGs: {agent_list}]\n\n"
    output += "=" * 70 + "\n"

    # Display each agent's response clearly
    for i, (agent_id, response) in enumerate(responses.items(), 1):
        output += f"\n📋 {agent_id.upper()} TWG Response:\n"
        output += "-" * 70 + "\n"
        output += response + "\n"

        if i < len(responses):  # Not the last one
            output += "\n" + "=" * 70 + "\n"

    output += "\n" + "=" * 70 + "\n"

    # Build synthesis prompt for the supervisor
    synthesis_prompt = f"""Original Question: {query}

I have consulted {len(responses)} TWG agents and received these responses:

"""
    for agent_id, response in responses.items():
        synthesis_prompt += f"\n{agent_id.upper()} TWG:\n{response}\n"

    synthesis_prompt += "\n\nAs the Supervisor, provide a brief (2-3 sentence) strategic synthesis that highlights how these TWG perspectives complement each other and what the key takeaways are."

    # Get supervisor's synthesis
    synthesis = supervisor_agent.chat(synthesis_prompt)

    # Add synthesis at the end
    output += f"\n🎯 SUPERVISOR'S SYNTHESIS:\n"
    output += "-" * 70 + "\n"
    output += synthesis + "\n"

    # --- CONFLICT DETECTION LAYER ---
    # In a production system, this would be a separate node possibly running in parallel
    if len(responses) > 1:
        logger.info("[SYNTHESIS] Running Conflict Detection Layer...")
        conflict_prompt = f"""
        Review the responses above for any direct contradictions, schedule clashes, or resource conflicts.
        
        Responses:
        {chr(10).join([f"{k}: {v}" for k, v in responses.items()])}
        
        If a significant conflict exists, respond with "CONFLICT DETECTED" and a brief explanation.
        Otherwise, respond "NO CONFLICT".
        """
        
        try:
            # We use the same agent for detection for now
            conflict_check = supervisor_agent.chat(conflict_prompt)
            
            if "CONFLICT DETECTED" in conflict_check.upper():
                output += f"\n\n⚠️ CONFLICT PROTOCOL ACTIVATED:\n"
                output += conflict_check
                logger.warning(f"Conflict Detected: {conflict_check}")
                # Future: await save_conflict_to_db(...)
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")

    state["synthesized_response"] = synthesis
    state["final_response"] = output

    logger.info(f"[SYNTHESIS] Complete")

    return state


# =========================================================================
# SINGLE AGENT RESPONSE NODE - Format single agent response
# =========================================================================

def single_agent_response_node(state: AgentState) -> AgentState:
    """
    Format response from a single TWG agent.
    """
    responses = state["agent_responses"]

    if not responses:
        state["final_response"] = "No response received from agent."
        return state

    # Get the single agent's response
    agent_id, response = list(responses.items())[0]

    # Add context header
    context = f"[Consulted {agent_id.upper()} TWG]\n\n{response}"

    state["final_response"] = context

    logger.info(f"[SINGLE] Formatted response from {agent_id}")

    return state
