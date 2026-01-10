"""
LangGraph Node Functions for Multi-Agent System

Each function represents a node in the agent graph.
"""

from typing import Dict, List
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage

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

    # Agent domain keywords
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
    def twg_node(state: AgentState) -> AgentState:
        """
        Delegate query to a specific TWG agent.
        """
        query = state["query"]
        logger.info(f"[{agent_id.upper()}] Processing query")

        try:
            response = agent.chat(query)
            state["agent_responses"][agent_id] = response
            logger.info(f"[{agent_id.upper()}] Response generated")
        except Exception as e:
            logger.error(f"[{agent_id.upper()}] Error: {e}")
            state["agent_responses"][agent_id] = f"Error: {str(e)}"

        return state

    return twg_node


# =========================================================================
# SYNTHESIS NODE - Combine responses from multiple agents
# =========================================================================

def synthesis_node(state: AgentState, supervisor_agent: LangGraphBaseAgent) -> AgentState:
    """
    Synthesize responses from multiple TWG agents into ONE unified professional memo.
    """
    query = state["query"]
    responses = state["agent_responses"]

    if not responses:
        state["final_response"] = "I couldn't get responses from the relevant agents."
        return state

    logger.info(f"[SYNTHESIS] Synthesizing {len(responses)} TWG responses into unified memo")

    # Truncate responses AGGRESSIVELY to prevent 413 errors
    truncated_responses = {}
    for agent_id, response in responses.items():
        # Limit to 300 characters (~75 tokens) - very aggressive
        if len(response) > 300:
            truncated_responses[agent_id] = response[:300] + "..."
        else:
            truncated_responses[agent_id] = response

    # Build synthesis prompt for unified memo - keep it SHORT to avoid token limits
    agent_list = ", ".join([agent_id.upper() for agent_id in responses.keys()])

    synthesis_prompt = f"""Question: {query}

TWG Inputs ({agent_list}):
"""
    for agent_id, response in truncated_responses.items():
        synthesis_prompt += f"\n{agent_id}: {response}\n"

    synthesis_prompt += f"""
Write ONE professional memo (max 500 words, NO emojis) synthesizing these TWG inputs.
Format: Executive Summary, Strategic Rationale, Financial Overview, Regional Impact, Recommendation."""

    # Get supervisor's unified memo
    try:
        unified_memo = supervisor_agent.chat(synthesis_prompt)
        output = unified_memo
    except Exception as e:
        logger.error(f"[SYNTHESIS] Synthesis generation failed: {e}")
        output = f"Error generating unified memo: {str(e)}\n\nPlease review the request and try again."

    # --- CONFLICT DETECTION LAYER ---
    # Check for conflicts between TWG responses
    if len(responses) > 1:
        logger.info("[SYNTHESIS] Running Conflict Detection Layer...")
        conflict_prompt = f"""
        Review these TWG inputs for any direct contradictions, schedule clashes, or resource conflicts:

        {chr(10).join([f"{k}: {v[:500]}" for k, v in truncated_responses.items()])}

        If a significant conflict exists, respond with "CONFLICT DETECTED" and a brief explanation.
        Otherwise, respond "NO CONFLICT".
        """

        try:
            conflict_check = supervisor_agent.chat(conflict_prompt)

            if "CONFLICT DETECTED" in conflict_check.upper():
                output += f"\n\nCONFLICT ALERT:\n{conflict_check}"
                logger.warning(f"Conflict Detected: {conflict_check}")
                # Future: await save_conflict_to_db(...)
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")

    state["synthesized_response"] = output
    state["final_response"] = output

    logger.info(f"[SYNTHESIS] Complete - Generated unified memo")

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
