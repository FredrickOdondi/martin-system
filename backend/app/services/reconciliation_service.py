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
    Meeting, MeetingStatus, Conflict, ConflictStatus, ConflictType, TWG, User, MeetingParticipant, VipProfile,
    Notification, NotificationType, UserRole
)
from app.core.config import settings


from app.services.dependency_service import DependencyService

class ReconciliationService:
    """
    The "Air Traffic Controller" for the summit.
    Orchestrates multi-agent negotiation to resolve conflicts automatically.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_client = None
        self.dependency_service = DependencyService(db)

    # ... (skipping unchanged methods) ...

    async def _notify_escalation(self, conflict: Conflict):
        """
        Notify Admins and Secretariat Leads about the escalation.
        """
        try:
            # 1. Find target users
            stmt = select(User).where(
                User.role.in_([UserRole.ADMIN, UserRole.SECRETARIAT_LEAD])
            )
            result = await self.db.execute(stmt)
            recipients = result.scalars().all()
            
            # 2. Create Notifications
            notifications = []
            for user in recipients:
                notif = Notification(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    type=NotificationType.ALERT,
                    title=f"Conflict Escalated: {conflict.agents_involved[0] if conflict.agents_involved else 'Unknown'} vs ...",
                    content=f"Use Control Tower to resolve: {conflict.description}",
                    link="/admin/control-tower",
                    is_read=False,
                    created_at=datetime.datetime.utcnow()
                )
                notifications.append(notif)
            
            if notifications:
                self.db.add_all(notifications)
                # We do not commit here to ensure atomicity with the caller transaction or let caller decide
                # But actually run_automated_negotiation commits. So we should flush or rely on caller commit.
                # Given run_automated_negotiation does explicit commit for escalation, we can wait or do it there.
                print(f"🔔 Created {len(notifications)} escalation notifications.")
                
        except Exception as e:
            print(f"Failed to send escalation notifications: {e}")
    
    def _get_llm_client(self):
        """Get or create LLM client based on configured provider."""
        if self._llm_client is None:
            provider = getattr(settings, "LLM_PROVIDER", "ollama").lower()
            
            if provider == "github" and getattr(settings, "GITHUB_TOKEN", None):
                from openai import OpenAI
                self._llm_client = OpenAI(
                    api_key=settings.GITHUB_TOKEN,
                    base_url="https://models.github.ai/inference"
                )
                self._llm_model = getattr(settings, "GITHUB_MODEL", "gpt-4o-mini").replace("openai/", "")
            elif provider == "groq" and getattr(settings, "GROQ_API_KEY", None):
                from groq import Groq
                self._llm_client = Groq(api_key=settings.GROQ_API_KEY)
                self._llm_model = getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
            elif getattr(settings, "OPENAI_API_KEY", None):
                from openai import OpenAI
                self._llm_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self._llm_model = getattr(settings, "OPENAI_MODEL", "gpt-4-turbo-preview")
            else:
                raise RuntimeError(f"LLM Provider '{provider}' is not configured with required API keys.")
        return self._llm_client
    
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make an LLM call with the configured provider, with retries."""
        client = self._get_llm_client()
        
        import asyncio
        import random
        
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=self._llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content
            except Exception as e:
                is_rate_limit = "rate limit" in str(e).lower() or "too many requests" in str(e).lower() or "429" in str(e)
                
                if attempt < max_retries - 1 and is_rate_limit:
                    delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                    print(f"Warning: LLM Rate Limit hit. Retrying in {delay:.2f}s... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                else:
                    # Reraise or return error if last attempt or not rate limit
                    # Note: We wrap in RuntimeError to maintain interface contract
                    if is_rate_limit:
                        print(f"Error: LLM Rate Limit exhausted after {max_retries} attempts.")
                    raise RuntimeError(f"LLM call failed: {str(e)}")
    
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
                # Robust cleaning of LLM response
                clean_response = response.strip()
                if "```json" in clean_response:
                    clean_response = clean_response.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_response:
                    clean_response = clean_response.split("```")[1].split("```")[0].strip()
                
                # Find the JSON object
                start = clean_response.find('{')
                end = clean_response.rfind('}') + 1
                if start >= 0 and end > start:
                    result = json.loads(clean_response[start:end])
                    votes[twg_name] = result
                    continue
            except (json.JSONDecodeError, IndexError):
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
        Actually apply the resolution - update the actual meeting record.
        """
        if proposal.get("resolution_type") == "escalate_to_human":
            conflict.status = ConflictStatus.ESCALATED
            conflict.human_action_required = True
            await self.db.commit()
            return {"success": False, "reason": "Escalated to human review"}
        
        # Identify the affected meeting
        meeting_id = proposal.get("affected_meeting_id")
        if not meeting_id:
            return {"success": False, "reason": "No affected_meeting_id in proposal"}
            
        try:
            # Fetch the meeting
            stmt = select(Meeting).where(Meeting.id == uuid.UUID(meeting_id))
            res = await self.db.execute(stmt)
            meeting = res.scalar_one_or_none()
            
            if not meeting:
                return {"success": False, "reason": f"Meeting {meeting_id} not found"}
            
            res_type = proposal.get("resolution_type")
            action_taken = ""
            cascade_log = []
            
            # Application Logic
            if res_type == "shift_time":
                shift_mins = proposal.get("shift_minutes", 0)
                old_time = meeting.scheduled_at
                new_time = meeting.scheduled_at + datetime.timedelta(minutes=shift_mins)
                
                # Use DependencyService to handle cascade
                cascade_log = await self.dependency_service.propagate_changes(meeting, new_time)
                
                # Primary action description
                action_taken = f"Rescheduled: {old_time.strftime('%H:%M')} -> {new_time.strftime('%H:%M')}"
                if len(cascade_log) > 1:
                    action_taken += f" (+ {len(cascade_log)-1} downstream updates)"
                
            elif res_type == "change_venue":
                old_loc = meeting.location
                new_loc = proposal.get("action").split(" to ")[-1] if " to " in proposal.get("action") else "Virtual"
                meeting.location = new_loc
                action_taken = f"Moved Venue: {old_loc} -> {new_loc}"
                
            # Log the resolution
            conflict.status = ConflictStatus.RESOLVED
            conflict.resolved_at = datetime.datetime.utcnow()
            
            # Track change for notification
            log_entry = {
                "action": "auto_resolved",
                "resolution_type": res_type,
                "meeting_id": meeting_id,
                "change": action_taken,
                "proposal": proposal,
                "cascade_log": cascade_log,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            conflict.resolution_log = (conflict.resolution_log or []) + [log_entry]
            
            await self.db.commit()
            
            return {
                "success": True,
                "action_taken": action_taken or proposal.get("action"),
                "log": log_entry
            }
            
        except Exception as e:
            await self.db.rollback()
            return {"success": False, "reason": f"Execution error: {str(e)}"}
    
    def _calculate_priority(self, meeting: Meeting) -> int:
        """
        Deterministic Priority Score (0-10).
        Variables: VIP count, Keywords, Deadline.
        """
        score = 5  # Base score for standard meeting
        
        # 1. VIP/Minister Count
        # Assuming needed relations are loaded
        vip_count = 0
        has_minister = False
        if meeting.participants:
            for p in meeting.participants:
                if p.user and p.user.vip_profile:
                    vip_count += 1
                    title = p.user.vip_profile.title.lower() if p.user.vip_profile.title else ""
                    if "minister" in title or "head of state" in title:
                        has_minister = True
        
        score += vip_count * 1
        if has_minister:
            score += 3
            
        # 2. Keywords
        title = meeting.title.lower()
        if "summit" in title: score += 2
        if "signing" in title or "deal" in title: score += 2
        if "urgent" in title or "crisis" in title: score += 3
        
        # Cap at 10
        return min(score, 10)

    def _generate_algorithmic_compromises(
        self, 
        m1: Meeting, 
        m2: Meeting, 
        p1_score: int, 
        p2_score: int
    ) -> List[Dict[str, Any]]:
        """
        Programmatic generation of Compromise Options.
        Logic: Priority A > Priority B + 2 -> B moves. Else assume B moves for now (or propose both).
        """
        options = []
        
        # Determine who should move
        # If score diff is significant (>2), higher priority stays.
        if p1_score > p2_score + 2:
            mover = m2
            anchor = m1
        elif p2_score > p1_score + 2:
            mover = m1
            anchor = m2
        else:
            # Similar priority - propose moving the one with fewer participants? 
            # For simplicity, move the later one or m2
            mover = m2
            anchor = m1

        # Option 1: Sequential (Back-to-back)
        # Check if duration allows (e.g., both < 4h)
        if m1.duration_minutes + m2.duration_minutes < 480: # 8 hours max day?
            # Move mover to start 15 mins after anchor ends
            anchor_end = anchor.scheduled_at + datetime.timedelta(minutes=anchor.duration_minutes)
            new_start = anchor_end + datetime.timedelta(minutes=15)
            
            # Calculate shift in minutes
            shift_mins = (new_start - mover.scheduled_at).total_seconds() / 60
            
            options.append({
                "id": 1,
                "resolution_type": "shift_time",
                "action": f"Sequential: Move '{mover.title}' to {new_start.strftime('%H:%M')} (after '{anchor.title}')",
                "rationale": f"Avoid overlap by sequencing. Priority {anchor.title} ({max(p1_score, p2_score)}) retained.",
                "shift_minutes": shift_mins,
                "affected_meeting_id": str(mover.id),
                "confidence": 0.95
            })

        # Option 2: Virtual (If physical)
        if mover.location and mover.location.lower() not in ["virtual", "online", "remote"]:
            options.append({
                "id": 2,
                "resolution_type": "change_venue",
                "action": f"Virtual: Move '{mover.title}' to Virtual/Online Platform",
                "rationale": "Resolve venue conflict by switching to unlimited virtual capacity.",
                "affected_meeting_id": str(mover.id),
                "confidence": 0.8
            })
            
        # Option 3: Date Swap (Next Day)
        # Move to same time next day
        next_day = mover.scheduled_at + datetime.timedelta(days=1)
        options.append({
            "id": 3,
            "resolution_type": "shift_time",
            "action": f"Date Swap: Move '{mover.title}' to tomorrow ({next_day.strftime('%a %d')})",
            "rationale": "Defer lower priority meeting to next available slot to preserve duration.",
            "shift_minutes": 24 * 60, # 1 day
            "affected_meeting_id": str(mover.id),
            "confidence": 0.7
        })

        # Ensure we have 3 options
        while len(options) < 3:
             # Add a generic escalation or minor shift fallback
             fallback_mins = 60
             options.append({
                "id": len(options) + 1,
                "resolution_type": "shift_time",
                "action": f"Delay: Push '{mover.title}' by {fallback_mins} mins",
                "rationale": "Minor delay to reduce overlap overlap.",
                "shift_minutes": fallback_mins,
                "affected_meeting_id": str(mover.id),
                "confidence": 0.5
             })
             
        return options[:3]

    async def run_automated_negotiation(self, conflict: Conflict) -> Dict[str, Any]:
        """
        The complete "Debate Pattern" workflow with Deterministic Logic.
        """
        negotiation_log = []
        
        # Step 0: Load Conflicts with Meetings
        # We need the actual Meeting objects to calculate priority
        # conflicting_positions should have meeting IDs: {'meeting_1': 'uuid', 'meeting_2': 'uuid'}
        m1_id = conflict.conflicting_positions.get("meeting_1")
        m2_id = conflict.conflicting_positions.get("meeting_2")
        
        m1 = None
        m2 = None
        
        if m1_id and m2_id:
            try:
                # Load meetings with participants for scoring
                stmt = select(Meeting).where(Meeting.id.in_([uuid.UUID(m1_id), uuid.UUID(m2_id)])).options(
                    selectinload(Meeting.participants).selectinload(MeetingParticipant.user).selectinload(User.vip_profile)
                )
                r = await self.db.execute(stmt)
                meetings = r.scalars().all()
                m_map = {str(m.id): m for m in meetings}
                m1 = m_map.get(m1_id)
                m2 = m_map.get(m2_id)
            except Exception as e:
                print(f"Error loading meetings: {e}")

        # Step 1: Identify involved TWGs from the conflict
        agents_involved = conflict.agents_involved or []
        
        negotiation_log.append({
            "step": "identify_parties",
            "agents": agents_involved
        })
        
        # Step 2: Calculate Deterministic Priorities
        p1_score = self._calculate_priority(m1) if m1 else 5
        p2_score = self._calculate_priority(m2) if m2 else 5
        
        negotiation_log.append({
            "step": "priority_calculation",
            "scores": {
                m1.title if m1 else "M1": p1_score,
                m2.title if m2 else "M2": p2_score
            }
        })

        # Step 3: Query agents (keeping this for "Agent Input" / Constraints, but suppressing priority override)
        constraints = {}
        for twg_name in agents_involved:
            # We still ask for constraints (e.g. "VIP must attend") but we rely on our calc priority
            constraint = await self.query_agent_constraints(conflict, twg_name)
            
            # Inject our calculated priority if we can match the TWG
            # Simplified matching assumption: m1 belongs to agent[0] etc. 
            # For now just trust the calc score internally
            
            constraints[twg_name] = constraint

        # Step 4: Generate Algorithmic Proposals
        if m1 and m2:
            proposal_options = self._generate_algorithmic_compromises(m1, m2, p1_score, p2_score)
            proposal_data = {"options": proposal_options}
        else:
            # Fallback to LLM if we couldnt load meetings
            proposal_data = await self.supervisor_propose_resolution(conflict, constraints)

        negotiation_log.append({
            "step": "proposal_generation",
            "method": "algorithmic" if m1 and m2 else "llm_fallback",
            "proposal_data": proposal_data
        })
        
        # Step 5: Agents evaluate and vote
        votes = await self.agents_evaluate_proposal(conflict, constraints, proposal_data)
        negotiation_log.append({
            "step": "agent_votes",
            "votes": votes
        })
        
        # Step 6: Tally and Apply
        # ... (Reuse existing logic) ...
        vote_counts = {}
        for agent_vote in votes.values():
            choice = agent_vote.get("choice")
            vote_counts[choice] = vote_counts.get(choice, 0) + 1
            
        # Consensus Logic
        winning_choice = None
        num_agents = len(votes)
        
        # Majority wins
        for choice, count in vote_counts.items():
            if count > num_agents / 2: # Simple Majority
                winning_choice = choice
                break
                
        if winning_choice:
            winning_proposal = next(
                (opt for opt in proposal_data.get("options", []) if opt.get("id") == winning_choice), 
                None
            )
            
            if winning_proposal:
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
        
        # Escalation
        conflict.status = ConflictStatus.ESCALATED
        conflict.human_action_required = True
        conflict.resolution_log = (conflict.resolution_log or []) + [{
            "action": "escalated",
            "reason": "No consensus reached",
            "votes": votes,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }]
        
        # Notify Admins
        await self._notify_escalation(conflict)
        
        await self.db.commit()
        
        return {
            "negotiation_result": "escalated_to_human",
            "consensus_reached": False,
            "proposals_considered": proposal_data.get("options", []),
            "votes": votes,
            "negotiation_log": negotiation_log
        }

    async def ingest_weekly_packet(self, packet) -> Dict[str, Any]:
        """
        Process a TWG Weekly Packet:
        1. Create/Update proposed meetings.
        2. Resolve and create dependencies declared in the packet.
        3. Trigger conflict detection.
        """
        created_meetings = []
        created_dependencies = []
        errors = []
        
        # 1. Process Meetings
        title_to_id = {}
        
        # Fetch current user (Simulating Agent)
        # ideally this would be passed in or we assume system agent
        
        for meeting_data in packet.proposed_meetings:
            try:
                # Check if meeting exists by title + twg (simplified deduplication)
                # In prod, we might use a hash or specific ID if provided
                stmt = select(Meeting).where(
                    Meeting.twg_id == packet.twg_id,
                    Meeting.title == meeting_data.title
                )
                res = await self.db.execute(stmt)
                existing = res.scalar_one_or_none()
                
                if existing:
                    # Update fields? For now, skip or update schedule
                    existing.scheduled_at = meeting_data.scheduled_at
                    # ... update other fields
                    meeting_id = existing.id
                else:
                    # Create new
                    new_meeting = Meeting(
                        twg_id=packet.twg_id,
                        title=meeting_data.title,
                        scheduled_at=meeting_data.scheduled_at,
                        duration_minutes=meeting_data.duration_minutes,
                        location=meeting_data.location,
                        meeting_type=meeting_data.meeting_type,
                        status=MeetingStatus.SCHEDULED
                    )
                    self.db.add(new_meeting)
                    await self.db.flush() # Get ID
                    meeting_id = new_meeting.id
                    created_meetings.append(new_meeting)
                
                title_to_id[meeting_data.title] = meeting_id
                
            except Exception as e:
                errors.append(f"Error processing meeting '{meeting_data.title}': {str(e)}")

        # 2. Process Dependencies
        from app.models.models import MeetingDependency, DependencySource
        
        for dep_decl in packet.dependencies:
            try:
                # Resolve Source
                source_id = title_to_id.get(dep_decl.source_meeting_title)
                if not source_id:
                    # Try finding in DB (fuzzy match? exact match for now)
                    stmt = select(Meeting.id).where(Meeting.title == dep_decl.source_meeting_title)
                    res = await self.db.execute(stmt)
                    source_id = res.scalar_one_or_none()
                
                # Resolve Target
                target_id = title_to_id.get(dep_decl.target_meeting_title)
                if not target_id:
                     stmt = select(Meeting.id).where(Meeting.title == dep_decl.target_meeting_title)
                     res = await self.db.execute(stmt)
                     target_id = res.scalar_one_or_none()
                
                if source_id and target_id:
                    # Create Dependency
                    # Check existing?
                    dep = MeetingDependency(
                        source_meeting_id=source_id,
                        target_meeting_id=target_id,
                        dependency_type=dep_decl.dependency_type,
                        source_type=DependencySource.TWG_PACKET,
                        confidence_score=1.0, 
                        created_by_agent=f"TWG-{packet.twg_id}" # Simple placeholder
                    )
                    self.db.add(dep)
                    created_dependencies.append(dep)
                else:
                    errors.append(f"Could not resolve dependency: '{dep_decl.source_meeting_title}' -> '{dep_decl.target_meeting_title}'")
            
            except Exception as e:
                errors.append(f"Error processing dependency: {str(e)}")

        await self.db.commit()
        
        return {
            "created_meetings": len(created_meetings),
            "created_dependencies": len(created_dependencies),
            "errors": errors
        }

    async def propose_resolution(self, conflict: Conflict) -> Dict[str, Any]:
        """Legacy method - now just calls the full negotiation."""
        result = await self.run_automated_negotiation(conflict)
        return {
            "conflict_id": str(conflict.id),
            "proposals": [result.get("winning_proposal", {})], # Return winning if any
            "recommended": result.get("winning_proposal"),
            "requires_human_approval": result.get("negotiation_result") == "escalated_to_human"
        }

def get_reconciliation_service(db: AsyncSession) -> ReconciliationService:
    """Factory function."""
    return ReconciliationService(db)
