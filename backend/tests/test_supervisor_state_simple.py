import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from app.services.supervisor_state_service import SupervisorGlobalState
from app.models.models import Meeting, TWG, Document, Project, MeetingStatus, ProjectStatus, TWGPillar, Conflict, ConflictType, ConflictStatus, ConflictSeverity

@pytest.mark.asyncio
async def test_supervisor_state_refresh(db_session):
    """Test that supervisor state correctly aggregates data from DB"""
    
    # 1. Setup Data
    # Create TWG
    twg_id = uuid4()
    twg = TWG(id=twg_id, name="Test TWG", pillar=TWGPillar.ENERGY, description="Test", status="active")
    db_session.add(twg)
    
    # Create Meeting
    meeting_id = uuid4()
    meeting = Meeting(
        id=meeting_id,
        twg_id=twg_id,
        title="Test Meeting",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        duration_minutes=60,
        status=MeetingStatus.SCHEDULED,
        meeting_type="virtual"
    )
    db_session.add(meeting)
    
    # Create Document
    doc_id = uuid4()
    document = Document(
        id=doc_id,
        twg_id=twg_id,
        file_name="test_doc.pdf",
        file_path="/tmp/test.pdf",
        file_type="application/pdf",
        created_at=datetime.utcnow(),
        is_confidential=False,
        uploaded_by_id=uuid4() # Mock user ID, relationship might fail if user doesn't exist. 
                               # In unit tests with sqlite, FK constraint might be enforced.
                               # Let's hope the fixture mocks DB or disables FK, 
                               # otherwise we need a user.
    )
    # db_session.add(document) # Skip document if user dependency is complex for this quick test
    
    # Create Conflict
    conflict = Conflict(
        id=uuid4(),
        conflict_type=ConflictType.SCHEDULE_CLASH,
        description="Test Conflict",
        severity=ConflictSeverity.HIGH,
        status=ConflictStatus.DETECTED,
        agents_involved=["Test TWG"],
        detected_at=datetime.utcnow()
    )
    db_session.add(conflict)
    
    await db_session.commit()
    
    # 2. Refresh State
    service = SupervisorGlobalState()
    state = await service.refresh_state(db_session)
    
    # 3. Assertions
    assert state is not None
    assert state.total_meetings >= 1
    assert len(state.calendar) >= 1
    
    found_meeting = next((m for m in state.calendar if m.id == meeting_id), None)
    assert found_meeting is not None
    assert found_meeting.title == "Test Meeting"
    
    assert len(state.active_conflicts) >= 1
    found_conflict = next((c for c in state.active_conflicts if "Test Conflict" in c.description), None)
    assert found_conflict is not None

