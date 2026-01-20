"""
Negotiation Service

Facilitates automated negotiation between TWG agents to resolve conflicts.
Refactored to support:
- Database integration (Conflict model)
- Counter-proposal logic
- Multi-round debate
- Context-aware resource trading
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, UTC
from loguru import logger
from uuid import UUID
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.models import Conflict, ConflictStatus, Meeting, User, TWG, MeetingParticipant
from app.services.llm_service import get_llm_service

class NegotiationService:
    """
    Orchestrates "True AI Multi-Agent Negotiation" (Debate Pattern).
    
    Instead of just voting on pre-defined options, this service facilitates 
    a counter-proposal loop where agents can:
    1. Reject proposals with specific reasons (constraints).
    2. Offer conditional compromises ("I'll move if you give me the Main Hall").
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_service = get_llm_service()

    async def initiate_negotiation(
        self,
        trigger_user_id: Optional[UUID],
        topic: str,
        participating_twg_ids: List[UUID],
        context_data: Dict[str, Any]
    ) -> Conflict:
        """
        Start a new negotiation. Creates or updates a Conflict record.
        """
        # 1. Resolve TWG names
        # We need names for the agents_involved list
        stmt = select(TWG).where(TWG.id.in_(participating_twg_ids))
        twgs = (await self.db.execute(stmt)).scalars().all()
        agent_names = [twg.pillar.value for twg in twgs] # e.g. "energy_infrastructure"
        
        # 2. Check if active conflict exists for this topic?
        # For now, always create a new one or use the one passed in context if available
        conflict_id = context_data.get("conflict_id")
        
        if conflict_id:
            stmt = select(Conflict).where(Conflict.id == UUID(conflict_id))
            conflict = (await self.db.execute(stmt)).scalar_one_or_none()
            if conflict:
                # Reset status if needed
                if conflict.status in [ConflictStatus.RESOLVED, ConflictStatus.DISMISSED]:
                    conflict.status = ConflictStatus.NEGOTIATING
                    conflict.resolution_log = (conflict.resolution_log or []) + [{
                        "action": "reopened",
                        "timestamp": datetime.utcnow().isoformat()
                    }]
                return conflict
        
        # Create new Conflict record if not found
        import uuid
        new_conflict = Conflict(
            id=uuid.uuid4(),
            conflict_type="schedule_clash", # default, can be updated
            severity="medium",
            description=topic,
            agents_involved=agent_names,
            conflicting_positions=context_data.get("positions", {}),
            status=ConflictStatus.NEGOTIATING,
            metadata_json={"twg_ids": [str(t.id) for t in twgs], **context_data}
        )
        self.db.add(new_conflict)
        await self.db.flush()
        return new_conflict

    async def run_negotiation(self, conflict_id: UUID, max_rounds: int = 4) -> Dict[str, Any]:
        """
        Run the multi-round negotiation loop.
        """
        stmt = select(Conflict).where(Conflict.id == conflict_id)
        conflict = (await self.db.execute(stmt)).scalar_one_or_none()
        
        if not conflict:
            raise ValueError(f"Conflict {conflict_id} not found")
        
        # Load Context (Meetings, VIPs, etc.)
        context_str = await self._build_deep_context(conflict)
        
        # Negotiation State
        round_num = 1
        history = []
        
        # Start the Loop
        while round_num <= max_rounds:
            logger.info(f"🔄 Negotiation Round {round_num} for {conflict_id}")
            
            # 1. Generate Proposals / Counter-Proposals
            proposals = await self._generate_agent_proposals(conflict, context_str, history)
            
            # Log this round
            round_entry = {
                "round": round_num,
                "timestamp": datetime.utcnow().isoformat(),
                "proposals": proposals
            }
            history.append(round_entry)
            
            # 2. Supervisor Analysis
            analysis = await self._supervisor_analyze(conflict, context_str, history)
            
            if analysis.get("has_consensus"):
                # Success!
                await self._finalize_resolution(conflict, analysis, history)
                return {
                    "status": "CONSENSUS_REACHED",
                    "summary": f"Resolved in {round_num} rounds.",
                    "agreement_text": analysis.get("agreement_text"),
                    "history": history
                }
            
            # 3. Guidance for next round (updated into context)
            guidance = analysis.get("guidance", "Please try to find a middle ground.")
            context_str += f"\n\n[SUPERVISOR GUIDANCE]: {guidance}"
            
            round_num += 1
            
        # If loop finishes without consensus
        await self._escalate_conflict(conflict, history)
        return {
            "status": "ESCALATED",
            "summary": "Max rounds reached without consensus.",
            "history": history
        }

    async def _build_deep_context(self, conflict: Conflict) -> str:
        """
        Fetch DB Objects (Meetings, Profiles) to give the LLM 'Reasoning Power'.
        """
        context = f"CONFLICT: {conflict.description}\n"
        
        # Extract meeting IDs from metadata/positions
        # Assuming positions format: {'agent_name': {'meeting_id': 'uuid'}}
        # or metadata: {'meeting_ids': ['uuid', 'uuid']}
        meeting_ids = []
        
        # Look in metadata first (more reliable if we populate it)
        if conflict.metadata_json and "meeting_ids" in conflict.metadata_json:
             meeting_ids = conflict.metadata_json["meeting_ids"]
        
        # Use positions as fallback
        elif conflict.conflicting_positions:
             for pos in conflict.conflicting_positions.values():
                 if isinstance(pos, dict) and "meeting_id" in pos:
                     meeting_ids.append(pos["meeting_id"])

        if meeting_ids:
            # Query DB
            stmt = select(Meeting).where(
                Meeting.id.in_([UUID(mid) for mid in meeting_ids])
            ).options(
                selectinload(Meeting.participants).selectinload(MeetingParticipant.user).selectinload(User.vip_profile),
                selectinload(Meeting.twg)
            )
            res = (await self.db.execute(stmt)).scalars().all()
            
            context += "\nINVOLVED EVENTS:\n"
            for m in res:
                vip_names = [
                    f"{p.user.full_name} ({p.user.vip_profile.title})" 
                    for p in m.participants 
                    if p.user and p.user.vip_profile
                ]
                context += f"- Event: {m.title}\n"
                context += f"  Time: {m.scheduled_at}\n"
                context += f"  Location: {m.location}\n"
                context += f"  Owner: {m.twg.name} TWG\n"
                context += f"  VIPs: {', '.join(vip_names) if vip_names else 'None'}\n"
                context += f"  Duration: {m.duration_minutes} mins\n\n"
                
        return context

    async def _generate_agent_proposals(self, conflict: Conflict, context: str, history: List[Dict]) -> Dict[str, str]:
        """
        Ask each agent for their move.
        """
        proposals = {}
        
        history_text = ""
        if history:
            history_text = "\nNEGOTIATION HISTORY:\n"
            for h in history:
                history_text += f"\nRound {h['round']}:\n"
                for agent, prop in h['proposals'].items():
                    history_text += f"  {agent}: {prop}\n"
        
        for agent_name in conflict.agents_involved:
            # Persona Prompt
            system_prompt = f"""You are the {agent_name} Agent for the ECOWAS Summit.
You are in a high-stakes negotiation to resolve a conflict.

Your Goal:
1. Protect your key constraints (VIPs, deadlines).
2. BE CREATIVE. Propose specific trades (e.g. "I move to 4pm if I get the big room").
3. Seeking solution. Do not just say "No". Offer "Yes, if...".

CONTEXT:
{context}

{history_text}
"""
            user_prompt = "What is your proposal for this round? (Be concise, 1-2 sentences)"
            
            try:
                response = self.llm_service.chat(
                    prompt=user_prompt,
                    system_prompt=system_prompt
                )
                proposals[agent_name] = response
            except Exception as e:
                logger.error(f"Agent {agent_name} failed to propose: {e}")
                proposals[agent_name] = "Abstain due to error."
                
        return proposals

    async def _supervisor_analyze(self, conflict: Conflict, context: str, history: List[Dict]) -> Dict[str, Any]:
        """
        The Supervisor judges if the latest proposals converge.
        """
        last_round = history[-1]
        
        system_prompt = """You are the Secretariat Martin (Supervisor).
Review the latest negotiation proposals.
Determine if CONSENSUS has been reached.

Consensus Rules:
- All parties successfully agreed to a specific plan.
- Or one party conceded and the other accepted.
- No "open questions" remain.

Output JSON:
{
    "has_consensus": boolean,
    "agreement_text": "text summary of the deal" or null,
    "guidance": "advice for next round if not resolved"
}
"""
        user_prompt = f"""CONTEXT:
{context}

LATEST ROUND PROPOSALS:
{json.dumps(last_round['proposals'], indent=2)}
"""
        response = self.llm_service.chat(
            prompt=user_prompt,
            system_prompt=system_prompt
        )
        
        # Parse JSON
        try:
            # Clean markdown code blocks if any
            clean_res = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_res)
        except Exception:
            logger.warning(f"Failed to parse Supervisor JSON: {response}")
            return {"has_consensus": False, "guidance": "Keep talking."}

    async def _finalize_resolution(self, conflict: Conflict, analysis: Dict[str, Any], history: List[Dict]):
        """
        Save the win.
        """
        conflict.status = ConflictStatus.RESOLVED
        conflict.resolved_at = datetime.utcnow()
        conflict.resolution_log = (conflict.resolution_log or []) + [{
            "action": "resolved",
            "agreement": analysis.get("agreement_text"),
            "history": history,
            "timestamp": datetime.utcnow().isoformat()
        }]
        await self.db.commit()

    async def _escalate_conflict(self, conflict: Conflict, history: List[Dict]):
        """
        Give up and call a human.
        """
        conflict.status = ConflictStatus.ESCALATED
        conflict.human_action_required = True
        conflict.resolution_log = (conflict.resolution_log or []) + [{
            "action": "escalated_max_rounds",
            "history": history,
            "timestamp": datetime.utcnow().isoformat()
        }]
        await self.db.commit()
