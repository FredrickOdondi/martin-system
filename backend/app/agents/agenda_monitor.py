from app.services.llm_service import get_llm_service
from typing import List, Dict, Any, Optional
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class AgendaMonitor:
    def __init__(self):
        self.llm = get_llm_service() 

    async def analyze(self, transcript_chunk: str, agenda_text: str) -> Dict[str, Any]:
        """
        Analyzes the transcript chunk against the agenda to determine current topic and progress.
        runs in a thread to avoid blocking the async event loop.
        """
        if not transcript_chunk or not agenda_text:
            return {}

        prompt = f"""
        You are an AI Agenda Monitor for a meeting.
        
        AGENDA:
        {agenda_text}
        
        RECENT TRANSCRIPT:
        {transcript_chunk}
        
        Task:
        1. Identify which agenda item is currently being discussed (by index or similarity).
        2. Determine if any items have been completed ("Discussed").
        3. Extract any key decisions made in this chunk.
        
        Return ONLY valid JSON in the following format:
        {{
            "current_item_index": <int (0-based) or null>,
            "current_item_title": <string or null>,
            "completed_items_indices": [<list of ints>],
            "decisions": [<list of strings>]
        }}
        """
        
        try:
            # Run blocking LLM call in a thread
            response_text = await asyncio.to_thread(
                self.llm.chat, 
                prompt=prompt, 
                temperature=0.1, 
                max_tokens=512
            )
            
            # Clean up JSON (sometimes LLMs add backticks)
            cleaned_text = response_text.strip().replace('```json', '').replace('```', '')
            data = json.loads(cleaned_text)
            return data
        except Exception as e:
            logger.error(f"Agenda Monitor Error: {e}")
            return {}
