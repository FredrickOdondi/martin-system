from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
from app.services.calendar_service import calendar_service


async def get_schedule(days: int = 7, twg_id: Optional[str] = None) -> str:
    """
    Fetch the calendar schedule for the next N days from the internal database.
    
    Args:
        days: Number of days to look ahead (default: 7)
        twg_id: Optional TWG ID to filter meetings by.
        
    Returns:
        JSON string of calendar events
    """
    from app.core.database import AsyncSessionLocal
    from app.models.models import Meeting
    from sqlalchemy import select, and_
    import uuid
    
    try:
        # Calculate time range
        now = datetime.utcnow()
        end_date = now + timedelta(days=days)
        
        async with AsyncSessionLocal() as session:
            # Build query with optional TWG filter
            conditions = [
                Meeting.scheduled_at >= now,
                Meeting.scheduled_at <= end_date
            ]
            
            if twg_id:
                try:
                    # Validate UUID format
                    twg_uuid = uuid.UUID(twg_id)
                    conditions.append(Meeting.twg_id == twg_uuid)
                except ValueError:
                    return json.dumps({"error": f"Invalid TWG ID format: {twg_id}"})
            
            query = select(Meeting).where(and_(*conditions)).order_by(Meeting.scheduled_at)
            
            result = await session.execute(query)
            meetings = result.scalars().all()
            
            if not meetings:
                msg = "No upcoming meetings found"
                if twg_id:
                    msg += f" for TWG {twg_id}"
                return json.dumps({"message": msg + "."})
            
            formatted_events = []
            for meeting in meetings:
                formatted_events.append({
                    "id": str(meeting.id),
                    "summary": meeting.title,
                    "start": meeting.scheduled_at.isoformat(),
                    "end": (meeting.scheduled_at + timedelta(minutes=meeting.duration_minutes)).isoformat(),
                    "status": meeting.status.value if hasattr(meeting.status, 'value') else meeting.status,
                    "meet_link": meeting.video_link,
                    "location": meeting.location,
                    "twg_id": str(meeting.twg_id)
                })
            
            return json.dumps(formatted_events, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Failed to fetch schedule from DB: {str(e)}"})

# Tool definition for LLM
GET_SCHEDULE_TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "get_schedule",
        "description": "Get the calendar schedule and events for the upcoming days. Use this to answer questions about availability or agenda.",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look ahead (default 7)",
                    "default": 7
                },
                "twg_id": {
                    "type": "string",
                    "description": "Optional TWG UUID to filter meetings by. If not provided, returns all meetings (Supervisor only)."
                }
            },
            "required": []
        }
    }
}
