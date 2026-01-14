from typing import List, Dict, Set, Optional, Any
import uuid
import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Meeting, MeetingDependency, DependencyType, MeetingStatus

class DependencyService:
    """
    Manages the directed graph of meeting dependencies.
    Enforces invariants (no cycles) and calculates cascading impacts.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_dependency(self, source_meeting_id: uuid.UUID, target_meeting_id: uuid.UUID, type: DependencyType = DependencyType.FINISH_TO_START, lag_minutes: int = 0) -> MeetingDependency:
        """
        Add a dependency Edge: Source -> Target
        Throws ValueError if a cycle is detected.
        """
        # 1. Check for self-dependency
        if source_meeting_id == target_meeting_id:
            raise ValueError("Cannot create dependency to self.")

        # 2. Check for existing dependency
        existing = await self.db.execute(
            select(MeetingDependency).where(
                MeetingDependency.source_meeting_id == source_meeting_id,
                MeetingDependency.target_meeting_id == target_meeting_id
            )
        )
        if existing.unique().scalar_one_or_none():
            raise ValueError("Dependency already exists.")

        # 3. Simulate adding edge and check for cycles
        # We need to load the graph to check cycles. 
        # For efficiency, we can do a localized BFS/DFS from target back to source.
        # If we can reach 'source' from 'target', then adding Source->Target creates a cycle.
        
        is_cyclic = await self._detect_cycle(start_node=target_meeting_id, target_node=source_meeting_id)
        if is_cyclic:
            raise ValueError("Cycle detected: This dependency would create a circular relationship.")

        # 4. Create Dependency
        dep = MeetingDependency(
            id=uuid.uuid4(),
            source_meeting_id=source_meeting_id,
            target_meeting_id=target_meeting_id,
            dependency_type=type,
            lag_minutes=lag_minutes
        )
        self.db.add(dep)
        await self.db.flush() # Flush to get ID but don't commit transaction yet
        return dep

    async def _detect_cycle(self, start_node: uuid.UUID, target_node: uuid.UUID) -> bool:
        """
        BFS to check if target_node is reachable from start_node.
        """
        visited = set()
        queue = [start_node]
        
        while queue:
            current = queue.pop(0)
            if current == target_node:
                return True
            
            if current in visited:
                continue
            visited.add(current)
            
            # Get successors of current
            stmt = select(MeetingDependency.target_meeting_id).where(MeetingDependency.source_meeting_id == current)
            result = await self.db.execute(stmt)
            successors = result.scalars().all()
            
            queue.extend(successors)
            
        return False

    async def get_cascading_impact(self, meeting: Meeting, new_start_time: datetime.datetime) -> List[Dict[str, Any]]:
        """
        If 'meeting' moves to 'new_start_time', which downstream meetings are violated?
        Returns a list of impacted meetings and the required shift.
        """
        impacted = []
        
        # Calculate new end time based on duration
        new_end_time = new_start_time + datetime.timedelta(minutes=meeting.duration_minutes)
        
        # Get immediate successors
        # We need to load them via db query if not lazy loaded
        stmt = select(MeetingDependency).where(MeetingDependency.source_meeting_id == meeting.id).options(selectinload(MeetingDependency.target_meeting))
        result = await self.db.execute(stmt)
        dependencies = result.scalars().all()
        
        for dep in dependencies:
            successor = dep.target_meeting
            required_start = None
            
            if dep.dependency_type == DependencyType.FINISH_TO_START:
                # Successor must start after Predecessor Ends (+ lag)
                min_start = new_end_time + datetime.timedelta(minutes=dep.lag_minutes)
                if successor.scheduled_at < min_start:
                    impacted.append({
                        "meeting_id": successor.id,
                        "title": successor.title,
                        "current_start": successor.scheduled_at,
                        "required_start": min_start,
                        "reason": f"Dependency violation: Must start after '{meeting.title}' ends + {dep.lag_minutes}m lag."
                    })
                    
                    # Basic Recursion? (Just 1 level for now or full graph?)
                    # For now, let's just return immediate impact to keep it simple.
                    # Full graph propagation is complex.
                    
        return impacted

    async def propagate_changes(self, meeting: Meeting, new_start_time: datetime.datetime) -> List[Dict[str, Any]]:
        """
        Recursively update downstream meetings to satisfy dependencies.
        Returns a log of changes made.
        """
        changes_log = []
        queue = [(meeting, new_start_time)]
        
        # Keep track to avoid infinite loops if something goes wrong (cycle check should prevent this though)
        processed = set() 
        
        while queue:
            current_meeting, current_start = queue.pop(0)
            if current_meeting.id in processed:
                continue
            processed.add(current_meeting.id)
            
            # 1. Update Current Meeting
            old_start = current_meeting.scheduled_at
            if old_start != current_start:
                current_meeting.scheduled_at = current_start
                changes_log.append({
                    "meeting_id": current_meeting.id,
                    "title": current_meeting.title,
                    "old_start": old_start,
                    "new_start": current_start,
                    "action": "propagated_from_dependency"
                })
            
            # 2. Check Successors
            current_end = current_start + datetime.timedelta(minutes=current_meeting.duration_minutes)
            
            # Query successors
            stmt = select(MeetingDependency).where(MeetingDependency.source_meeting_id == current_meeting.id).options(selectinload(MeetingDependency.target_meeting))
            result = await self.db.execute(stmt)
            dependencies = result.scalars().all()
            
            for dep in dependencies:
                successor = dep.target_meeting
                if dep.dependency_type == DependencyType.FINISH_TO_START:
                    min_start = current_end + datetime.timedelta(minutes=dep.lag_minutes)
                    if successor.scheduled_at < min_start:
                        # Add to queue to update successor
                        queue.append((successor, min_start))
                        
        return changes_log
