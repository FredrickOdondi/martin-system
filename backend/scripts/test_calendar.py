import sys
import os
import asyncio
from datetime import datetime

# Ensure we can import from app
sys.path.append(os.getcwd())

# Mock settings if needed, but we just want to test value
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/evan/Desktop/martin os v2/martin-system/backend/google_credentials.json"

from app.services.calendar_service import calendar_service

def test_calendar():
    print("Testing Calendar Service...")
    if not calendar_service.service:
        print("ERROR: Service not initialized. checking credentials...")
        if not os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]):
             print(f"ERROR: Credentials file not found at {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
        else:
             print("Credentials file exists.")
        return

    print("Service initialized. Attempting to create event...")
    try:
        event = calendar_service.create_meeting_event(
            title="Test Meeting from Script",
            start_time=datetime.utcnow(),
            duration_minutes=30,
            description="Testing API",
            attendees=[]
        )
        print("Result:", event)
        if event.get('hangoutLink'):
            print("SUCCESS: Link generated:", event.get('hangoutLink'))
        else:
            print("WARNING: Event created but NO link. Check conferenceDataVersion.")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    test_calendar()
