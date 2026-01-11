import asyncio
import uuid
from datetime import datetime, timedelta
from app.core.database import get_db_session_context
from app.models.models import User, VipProfile, TWG, Meeting, MeetingStatus, MeetingParticipant
from app.services.global_scheduler import global_scheduler

async def test_proactive_scheduling():
    async with get_db_session_context() as session:
        print("Setting up test data...")
        
        # 1. Create a VIP User
        vip_user = User(
            id=uuid.uuid4(),
            full_name="Minister Test",
            email=f"minister_{uuid.uuid4()}@example.com",
            hashed_password="hashed"
        )
        session.add(vip_user)
        await session.flush()
        
        vip_profile = VipProfile(
            user_id=vip_user.id,
            title="Minister of Testing",
            priority_level=5
        )
        session.add(vip_profile)
        
        # 2. Create a TWG
        twg = TWG(
            id=uuid.uuid4(),
            name="Energy TWG",
            pillar="energy_infrastructure"
        )
        session.add(twg)
        await session.flush()
        
        # 3. Schedule an existing meeting for the VIP at 10:00 - 11:00
        start_time = datetime(2026, 5, 20, 10, 0, 0)
        meeting = Meeting(
            id=uuid.uuid4(),
            twg_id=twg.id,
            title="Existing VIP Meeting",
            scheduled_at=start_time,
            duration_minutes=60,
            status=MeetingStatus.SCHEDULED
        )
        session.add(meeting)
        await session.flush()
        
        participant = MeetingParticipant(
            meeting_id=meeting.id,
            user_id=vip_user.id,
            rsvp_status="accepted"
        )
        session.add(participant)
        await session.commit()
        print("Test data setup complete.")

        # 4. Try to book a CONFLICTING meeting (same time)
        print("\n--- Test 1: Conflict Detection ---")
        result_conflict = await global_scheduler.request_booking(
            twg_id=twg.id,
            title="Conflicting Meeting",
            start_time=start_time, # Same start time
            duration_minutes=60,
            vip_attendee_ids=[vip_user.id],
            db=session # Reuse session? Or let it create new?
            # GlobalScheduler creates its own session if db is passed or not. 
            # Note: passing session might fail if we committed it and it's closed/clean? 
            # But here `session` is open. Let's see if GlobalScheduler handles passed session correctly. 
            # It uses `async with self._get_session(db)`. If db is passed, it uses it.
        )
        
        if result_conflict["status"] == "denied":
            print("✅ SUCCESS: Booking denied as expected.")
            print("Reason:", result_conflict["reason"])
            print("Conflicts:", [c["description"] for c in result_conflict["conflicts"]])
        elif result_conflict["status"] == "requested":
             print("⚠️  Warning: Booking was requested but not denied. (Maybe severity wasn't CRITICAL?)")
             print("Conflicts:", [c["description"] for c in result_conflict["conflicts"]])
        else:
            print("❌ FAILURE: Booking allowed despite conflict.")
            print(result_conflict)

        # 5. Try to book a NON-CONFLICTING meeting (different time)
        print("\n--- Test 2: Successful Booking ---")
        clean_start_time = start_time + timedelta(hours=3)
        result_success = await global_scheduler.request_booking(
            twg_id=twg.id,
            title="Clean Meeting",
            start_time=clean_start_time,
            duration_minutes=60,
            vip_attendee_ids=[vip_user.id],
            db=session
        )
        
        if result_success["status"] in ["scheduled", "requested"]:
            print(f"✅ SUCCESS: Booking {result_success['status']}.")
            print("Meeting ID:", result_success["meeting_id"])
        else:
             print("❌ FAILURE: Valid booking denied.")
             print(result_success)

if __name__ == "__main__":
    asyncio.run(test_proactive_scheduling())
