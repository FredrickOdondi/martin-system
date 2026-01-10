from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Dict, Any
import uuid

from app.models.models import TWG, Meeting, ActionItem, Conflict, Project, MeetingStatus, ActionItemStatus, ProjectStatus, WeeklyPacket

class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_twg_packet(self, twg_id: uuid.UUID, week_start: datetime, week_end: datetime) -> WeeklyPacket:
        """
        Simulates a TWG Sub-Agent generating its Weekly Packet.
        Gathering data from:
        - Meetings (Proposed Sessions)
        - Action Items & Projects (Accomplishments)
        - Conflicts (Risks)
        - Cross-referencing inputs (Dependencies)
        """
        
        # 1. Fetch Proposed Sessions (Meetings rescheduled or planned for next week)
        # For simplicity, we look at meetings scheduled for the *upcoming* week (assuming week_end is the end of 'this' week)
        next_week_start = week_end
        next_week_end = next_week_start + datetime.timedelta(days=7)
        
        upcoming_meetings_res = await self.db.execute(
            select(Meeting).where(
                Meeting.twg_id == twg_id,
                Meeting.scheduled_at >= next_week_start,
                Meeting.scheduled_at < next_week_end,
                Meeting.status == MeetingStatus.SCHEDULED
            )
        )
        upcoming_meetings = upcoming_meetings_res.scalars().all()
        
        proposed_sessions = []
        for m in upcoming_meetings:
            proposed_sessions.append({
                "title": m.title,
                "date": m.scheduled_at.isoformat(),
                "location": m.location or "TBD"
            })
            
        # 2. Accomlishments (Completed Items this week)
        completed_actions_res = await self.db.execute(
            select(ActionItem).where(
                ActionItem.twg_id == twg_id,
                ActionItem.status == ActionItemStatus.COMPLETED,
                ActionItem.due_date >= week_start, # Approximate "completed at" by using due_date or we'd need a completed_at field
            )
        )
        completed_actions = completed_actions_res.scalars().all()
        
        accomplishments = [f"Completed task: {a.description}" for a in completed_actions]
        
        # Add 'Signed' or 'Bankable' projects as accomplishments
        projects_res = await self.db.execute(
            select(Project).where(
                Project.twg_id == twg_id,
                Project.status.in_([ProjectStatus.BANKABLE, ProjectStatus.PRESENTED])
            )
        )
        projects = projects_res.scalars().all()
        for p in projects:
             accomplishments.append(f"Project '{p.name}' reached {p.status.value} status.")

        if not accomplishments:
             accomplishments.append("No major milestones recorded this week.")

        # 3. Risks & Blockers
        # Overdue items
        overdue_res = await self.db.execute(
            select(ActionItem).where(
                ActionItem.twg_id == twg_id,
                ActionItem.status == ActionItemStatus.OVERDUE
            )
        )
        overdue_items = overdue_res.scalars().all()
        
        risks = []
        for item in overdue_items:
            risks.append({
                "type": "Overdue Action",
                "description": f"Overdue: {item.description}",
                "severity": "medium"
            })

        # Stalled Projects (Status = Identified for long time? - Logic simplified here)
        stalled_projects_res = await self.db.execute(
            select(Project).where(Project.twg_id == twg_id, Project.status == ProjectStatus.VETTING)
        )
        stalled_projects = stalled_projects_res.scalars().all()
        for p in stalled_projects:
             risks.append({
                "type": "Stalled Negotiation",
                "description": f"Project '{p.name}' stuck in vetting.",
                "severity": "high"
             })

        # 4. Dependencies (Mock Analysis for now, real logic would scan project descriptions)
        # We can simulate this by looking for keywords of other Pillars in this TWG's docs
        dependencies = []
        # Placeholder logic: if "Energy" TWG has a project with "Agriculture" in description
        # For now, return empty or static placeholder if needed, but better to keep empty until real logic exists
        
        # Create and Persistence
        packet = WeeklyPacket(
            twg_id=twg_id,
            week_start_date=week_start,
            proposed_sessions=proposed_sessions,
            dependencies=dependencies,
            accomplishments=accomplishments,
            risks_and_blockers=risks,
            status="submitted"
        )
        
        self.db.add(packet)
        await self.db.commit()
        await self.db.refresh(packet)
        
        return packet
