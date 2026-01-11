
import asyncio
import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.supervisor_state_service import SupervisorGlobalState
from app.models.models import Meeting, TWG, Document, Project, MeetingStatus, ProjectStatus, TWGPillar, Conflict, ConflictType, ConflictStatus, ConflictSeverity, UserRole
from app.core.database import get_db_session_context

async def run_test():
    print("Starting Supervisor Global State Verification...")
    
    async with get_db_session_context() as session:
        # 1. Setup Data
        print("Seeding test data...")
        
        # Create TWG
        twg_id = uuid4()
        twg = TWG(id=twg_id, name=f"Test TWG {twg_id}", pillar=TWGPillar.energy_infrastructure, status="active")
        session.add(twg)
        
        # Create Meeting
        meeting_id = uuid4()
        meeting = Meeting(
            id=meeting_id,
            twg_id=twg_id,
            title="Test Meeting Global State",
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            duration_minutes=60,
            status=MeetingStatus.SCHEDULED,
            meeting_type="virtual"
        )
        session.add(meeting)
        
        # Create Conflict
        conflict_id = uuid4()
        conflict = Conflict(
            id=conflict_id,
            conflict_type=ConflictType.SCHEDULE_CLASH,
            description=f"Test Conflict {conflict_id}",
            severity=ConflictSeverity.HIGH,
            status=ConflictStatus.DETECTED,
            agents_involved=["Test TWG"],
            detected_at=datetime.utcnow(),
            conflicting_positions={}
        )
        session.add(conflict)
        
        await session.commit()
        
        # 2. Refresh State
        print("Refreshing global state...")
        service = SupervisorGlobalState()
        state = await service.refresh_state(session)
        
        # 3. Assertions
        print("Verifying state...")
        
        # Verify Meeting
        found_meeting = next((m for m in state.calendar if m.id == meeting_id), None)
        if found_meeting:
            print("✅ Meeting found in global calendar")
        else:
            print("❌ Meeting NOT found in global calendar")
            
        # Verify Conflict
        found_conflict = next((c for c in state.active_conflicts if c.id == conflict_id), None)
        if found_conflict:
            print("✅ Conflict found in active conflicts")
        else:
            print("❌ Conflict NOT found in active conflicts")
            
        # Verify TWG Summary
        summary = state.twg_summaries.get(str(twg_id))
        if summary:
            print("✅ TWG Summary found")
            if summary.total_meetings >= 1:
                print("✅ TWG Summary meeting count correct")
            else:
                print(f"❌ TWG Summary meeting count incorrect: {summary.total_meetings}")
        else:
            print("❌ TWG Summary NOT found")
        
    print("Verification complete.")

if __name__ == "__main__":
    asyncio.run(run_test())
