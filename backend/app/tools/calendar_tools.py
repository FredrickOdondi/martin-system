from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
from app.services.calendar_service import calendar_service

def get_schedule(days: int = 7) -> str:
    """
    Fetch the calendar schedule for the next N days.
    
    Args:
        days: Number of days to look ahead (default: 7)
        
    Returns:
        JSON string of calendar events
    """
    try:
        # Calculate time range
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'  # 'Z' indicates UTC time
        time_max = (now + timedelta(days=days)).isoformat() + 'Z'
        
        if not calendar_service.service:
            return json.dumps({"error": "Calendar service not initialized. Please authenticate on the backend."})

        events_result = calendar_service.service.events().list(
            calendarId='primary', 
            timeMin=time_min,
            timeMax=time_max,
            maxResults=50, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return json.dumps({"message": "No upcoming events found."})

        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            formatted_events.append({
                "summary": event.get('summary', 'No Title'),
                "start": start,
                "end": end,
                "link": event.get('htmlLink'),
                "meet_link": event.get('hangoutLink'),
                "description": event.get('description', '')
            })

        return json.dumps(formatted_events, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Failed to fetch schedule: {str(e)}"})

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
                }
            },
            "required": []
        }
    }
}
