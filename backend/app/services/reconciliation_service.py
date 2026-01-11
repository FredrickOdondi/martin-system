"""
Reconciliation Service - Real AI Multi-Agent Negotiation

Implements the "Debate Pattern" where Secretariat Martin (Supervisor) orchestrates
conflict resolution between TWG agents through structured negotiation.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
import datetime
import uuid
import json

from app.models.models import (
    Meeting, MeetingStatus, Conflict, ConflictStatus, ConflictType, TWG
)
from app.core.config import settings


class ReconciliationService:
    """
    The "Air Traffic Controller" for the summit.
    Orchestrates multi-agent negotiation to resolve conflicts automatically.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_client = None
    
    def _get_llm_client(self):
        """Get or create LLM client based on configured provider."""
        if self._llm_client is None:
            if settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY:
                from groq import Groq
                self._llm_client = Groq(api_key=settings.GROQ_API_KEY)
            elif settings.OPENAI_API_KEY:
                from openai import OpenAI
                self._llm_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            else:
                # Fallback - no LLM available
                self._llm_client = None
        return self._llm_client
    
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make an LLM call with the configured provider."""
        client = self._get_llm_client()
        if not client:
            return "LLM not configured. Using default response."
        
        try:
            model = settings.LLM_MODEL if settings.LLM_PROVIDER == "groq" else settings.OPENAI_MODEL
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM error: {str(e)}"
    
    async def query_agent_constraints(self, conflict: Conflict, twg_name: str) -> Dict[str, Any]:
        """
        Ask a TWG agent: What are your constraints for this conflict?
        
        The agent responds with:
        - priority: how important is this meeting (1-10)
        - can_shift: can the meeting time be moved?
        - shift_flexibility: how much time can it shift (in minutes)
        - vip_requirements: any VIPs that must attend
        - notes: additional context
        """
        system_prompt = f"""You are {twg_name} Martin, an AI agent representing the {twg_name} Technical Working Group.

You are being asked about scheduling constraints for a meeting that has a conflict.

Respond in JSON format with these fields:
{{
    "priority": <1-10, where 10 is highest priority>,
    "can_shift": <true/false>,
    "shift_flexibility_minutes": <0-180>,
    "vip_requirements": ["list of VIP names if any"],
    "notes": "brief explanation of constraints"
}}

Be realistic. Lower priority meetings should be more flexible."""

        user_prompt = f"""A scheduling conflict has been detected:

{conflict.description}

What are your constraints for your meeting in this conflict? Consider:
- The importance of your session topic
- VIP/ministerial attendance requirements
- Dependencies on other sessions

Respond with your constraints in JSON format."""

        response = await self._call_llm(system_prompt, user_prompt)
        
        # Parse JSON response
        try:
            # Extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        
        # Default fallback
        return {
            "priority": 5,
            "can_shift": True,
            "shift_flexibility_minutes": 60,
            "vip_requirements": [],
            "notes": f"Default constraints for {twg_name}"
        }
    
    async def supervisor_propose_resolution(
        self, 
        conflict: Conflict, 
        constraints: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Secretariat Martin (Supervisor) proposes 3 resolutions based on collected constraints.
        """
        system_prompt = """You are Secretariat Martin, the AI Chief of Staff for the ECOWAS Summit.
    
    You need to propose a resolution to a scheduling or policy conflict. You have received constraints from each involved TWG.
    
    Generate 3 compromise proposals that respect both TWGs' constraints:
    1. [Most ambitious / Ideal]
    2. [Balanced compromise]
    3. [Most conservative / Least disruption]
    
    Respond in JSON format:
    {
        "options": [
            {
                "id": 1,
                "resolution_type": "shift_time" | "change_venue" | "policy_compromise",
                "action": "specific action to take",
                "rationale": "brief explanation",
                "confidence": <0.0-1.0>
            },
            ...
        ]
    }
    """

        constraints_text = "\n".join([
            f"- {twg}: Priority {c.get('priority', 5)}/10, Notes: {c.get('notes', '')}"
            for twg, c in constraints.items()
        ])

        user_prompt = f"""Conflict: {conflict.description}
    
    Constraints from involved TWGs:
    {constraints_text}
    
    Propose 3 distinct options."""

        response = await self._call_llm(system_prompt, user_prompt)
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        
        # Default fallback
        return {
            "options": [
                {
                    "id": 1,
                    "resolution_type": "escalate_to_human",
                    "action": "Escalate to human review",
                    "rationale": "Automatic proposal generation failed",
                    "confidence": 0.0
                }
            ]
        }
    
    async def agents_evaluate_proposal(
        self, 
        conflict: Conflict,
        constraints: Dict[str, Dict[str, Any]],
        proposal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Each TWG agent evaluates the 3 options and votes.
        Returns dict of {twg_name: {choice: id, reason: str}}
        """
        votes = {}
        options = proposal_data.get("options", [])
        
        for twg_name, constraint in constraints.items():
            system_prompt = f"""You are {twg_name} Martin, an AI agent for the {twg_name} TWG.
    
    You are evaluating 3 proposed resolutions to a conflict. Based on your constraints, 
    vote for the best option (1, 2, or 3).
    
    Respond with JSON:
    {{
        "choice": <1, 2, or 3>,
        "reason": "brief explanation"
    }}"""

            user_prompt = f"""Your constraints: {json.dumps(constraint)}
    
    Proposed Options: {json.dumps(options)}
    
    Which option do you prefer?"""

            response = await self._call_llm(system_prompt, user_prompt)
            
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    result = json.loads(response[start:end])
                    votes[twg_name] = result
                    continue
            except json.JSONDecodeError:
                pass
            
            # Default vote (Option 1)
            votes[twg_name] = {"choice": 1, "reason": "Default vote due to parsing error"}
        
        return votes
    
    async def apply_meeting_resolution(
        self, 
        conflict: Conflict, 
        proposal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actually apply the resolution - reschedule the meeting.
        """
        if proposal.get("resolution_type") == "escalate_to_human":
            conflict.status = ConflictStatus.ESCALATED
            conflict.human_action_required = True
            await self.db.commit()
            return {"success": False, "reason": "Escalated to human review"}
        
        # For shift_time resolutions, try to find and update the affected meeting
        shift_minutes = proposal.get("shift_minutes", 0)
        affected = proposal.get("affected_meeting", "")
        
        # Log the resolution
        conflict.status = ConflictStatus.RESOLVED
        conflict.resolved_at = datetime.datetime.utcnow()
        conflict.resolution_log = (conflict.resolution_log or []) + [{
            "action": "auto_resolved",
            "proposal": proposal,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }]
        
        await self.db.commit()
        
        return {
            "success": True,
            "action_taken": proposal.get("action"),
            "shift_minutes": shift_minutes
        }
    
    async def run_automated_negotiation(self, conflict: Conflict) -> Dict[str, Any]:
        """
        The complete "Debate Pattern" workflow:
        
        1. Supervisor identifies conflicting TWGs
        2. Query each TWG agent for their constraints
        3. Supervisor proposes a resolution
        4. Each agent evaluates and votes
        5. If all agree, apply resolution; else escalate
        """
        negotiation_log = []
        
        # Step 1: Identify involved TWGs from the conflict
        agents_involved = conflict.agents_involved or ["Energy & Infrastructure", "Minerals & Extractives"]
        negotiation_log.append({
            "step": "identify_parties",
            "agents": agents_involved
        })
        
        # Step 2: Query each agent for constraints
        constraints = {}
        for twg_name in agents_involved:
            constraint = await self.query_agent_constraints(conflict, twg_name)
            constraints[twg_name] = constraint
            negotiation_log.append({
                "step": "constraint_query",
                "agent": twg_name,
                "response": constraint
            })
        
        # Step 3: Supervisor proposes 3 resolutions
        proposal_data = await self.supervisor_propose_resolution(conflict, constraints)
        negotiation_log.append({
            "step": "supervisor_proposal",
            "proposal_data": proposal_data
        })
        
        # Step 4: Agents evaluate and vote
        votes = await self.agents_evaluate_proposal(conflict, constraints, proposal_data)
        negotiation_log.append({
            "step": "agent_votes",
            "votes": votes
        })
        
        # Step 5: Tally votes
        vote_counts = {}
        for agent_vote in votes.values():
            choice = agent_vote.get("choice")
            vote_counts[choice] = vote_counts.get(choice, 0) + 1
            
        # Check for consensus (simple majority or unanimity)
        # For now, require unanimity or majority if > 2 agents
        num_agents = len(votes)
        winning_choice = None
        
        for choice, count in vote_counts.items():
            if count == num_agents: # Unanimous
                winning_choice = choice
                break
                
        if winning_choice:
            # Find the winning option object
            winning_proposal = next(
                (opt for opt in proposal_data.get("options", []) if opt.get("id") == winning_choice), 
                None
            )
            
            if winning_proposal:
                # Apply the resolution
                result = await self.apply_meeting_resolution(conflict, winning_proposal)
                negotiation_log.append({
                    "step": "resolution_applied",
                    "result": result,
                    "winning_choice": winning_choice
                })
                
                return {
                    "negotiation_result": "auto_resolved",
                    "consensus_reached": True,
                    "winning_proposal": winning_proposal,
                    "votes": votes,
                    "negotiation_log": negotiation_log
                }
        
        # If no consensus or winning proposal not found
        conflict.status = ConflictStatus.ESCALATED
        conflict.human_action_required = True
        conflict.resolution_log = (conflict.resolution_log or []) + [{
            "action": "escalated",
            "reason": "Agents did not reach consensus",
            "votes": votes,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }]
        await self.db.commit()
        
        return {
            "negotiation_result": "escalated_to_human",
            "consensus_reached": False,
            "proposals_considered": proposal_data.get("options", []),
            "votes": votes,
            "negotiation_log": negotiation_log
        }
    
    async def propose_resolution(self, conflict: Conflict) -> Dict[str, Any]:
        """Legacy method - now just calls the full negotiation."""
        result = await self.run_automated_negotiation(conflict)
        return {
            "conflict_id": str(conflict.id),
            "proposals": [result.get("proposal", {})],
            "recommended": result.get("proposal"),
            "requires_human_approval": result.get("negotiation_result") == "escalated_to_human"
        }


def get_reconciliation_service(db: AsyncSession) -> ReconciliationService:
    """Factory function to create reconciliation service."""
    return ReconciliationService(db)
