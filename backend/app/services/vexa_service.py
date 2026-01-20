
import aiohttp
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.models import Meeting, Minutes, MinutesStatus
from app.services.document_synthesizer import DocumentSynthesizer
from app.services.groq_llm_service import get_llm_service
from datetime import datetime

logger = logging.getLogger(__name__)

class VexaService:
    """
    Client service for Vexa Meeting Bot.
    """
    
    def __init__(self):
        self.api_url = settings.VEXA_API_URL
        self.api_key = settings.VEXA_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def join_meeting(self, meeting_url: str, meeting_id: str, bot_name: str = "Secretariat Bot") -> bool:
        """
        Dispatch a bot to join a meeting.
        """
        url = f"{self.api_url}/bots"
        
        # Parse meeting URL to determine platform and extract meeting ID
        if "meet.google.com" in meeting_url:
            platform = "google_meet"
            # Extract meeting code from URL (e.g., abc-defg-hij)
            native_meeting_id = meeting_url.split("/")[-1].split("?")[0]
        elif "teams.microsoft.com" in meeting_url:
            platform = "teams"
            # For Teams, we'd need the numeric ID and passcode
            # This is a simplified version
            native_meeting_id = meeting_url
        else:
            logger.warning(f"Unsupported meeting platform: {meeting_url}")
            return False
            
        payload = {
            "platform": platform,
            "native_meeting_id": native_meeting_id,
            "bot_name": bot_name
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=self.headers) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        logger.info(f"Vexa Bot dispatched to {meeting_url}. Session ID: {data.get('sessionId')}")
                        return True
                    else:
                        text = await response.text()
                        logger.error(f"Failed to dispatch Vexa bot: {response.status} - {text}")
                        return False
        except Exception as e:
            logger.error(f"Error connecting to Vexa API: {e}")
            return False

    async def check_active_sessions(self):
        """
        Check status of active bots and retrieve transcripts if finished.
        This could be run periodically by continuous monitor.
        """
        url = f"{self.api_url}/v1/sessions"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        sessions = await response.json()
                        for sess in sessions:
                            if sess.get('status') == 'completed':
                                await self._process_completed_session(sess)
        except Exception as e:
            logger.error(f"Error checking Vexa sessions: {e}")

    async def _process_completed_session(self, session_data: Dict[str, Any]):
        """
        Retrieve final transcript and save as minutes.
        """
        session_id = session_data.get('sessionId')
        meeting_db_id = session_data.get('metadata', {}).get('meeting_id')
        
        if not meeting_db_id:
            logger.warning(f"Completed session {session_id} has no meeting_id metadata.")
            return

        # Fetch Transcript
        transcript_url = f"{self.api_url}/v1/sessions/{session_id}/transcript"
        transcript_text = ""
        
        try:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(transcript_url, headers=self.headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Assuming Vexa returns list of segments or full text field
                        # Simplify: just dumping JSON for now or text field if exists
                        transcript_text = data.get('text', json.dumps(data)) 
                    else:
                        logger.error(f"Failed to get transcript for {session_id}")
                        return
        except Exception as e:
            logger.error(f"Error fetching transcript: {e}")
            return

        # Save to DB
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            stmt = select(Meeting).where(Meeting.id == meeting_db_id)
            result = await db.execute(stmt)
            meeting = result.scalar_one_or_none()
            
            if meeting:
                logger.info(f"Saving Vexa transcript for {meeting.title}")
                meeting.transcript = transcript_text
                
                # Auto-generate minutes using Synthesizer (re-using logic from DriveService basically)
                # For MVP, just saving transcript is huge win.
                # If we want minutes:
                try:
                     synthesizer = DocumentSynthesizer(llm_client=get_llm_service())
                     minutes_ctx = {
                         "meeting_title": meeting.title,
                         "meeting_date": str(meeting.scheduled_at),
                         "attendees_list": "See transcript (Vexa)"
                     }
                     # Blocking call in thread
                     res = await asyncio.to_thread(synthesizer.synthesize_minutes, transcript_text, minutes_ctx)
                     
                     new_minutes = Minutes(
                        meeting_id=meeting.id,
                        content=res['content'],
                        status=MinutesStatus.DRAFT
                     )
                     db.add(new_minutes)
                     meeting.minutes = new_minutes
                     logger.info(f"Generated Minutes for {meeting.title} from Vexa")
                except Exception as synth_err:
                    logger.error(f"Failed to synthesize minutes from Vexa transcript: {synth_err}")

                await db.commit()
            else:
                logger.warning(f"Meeting DB ID {meeting_db_id} not found for Vexa session.")

vexa_service = VexaService()
