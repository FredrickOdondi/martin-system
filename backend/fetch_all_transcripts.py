import asyncio
import aiohttp
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.services.vexa_service import vexa_service
from app.models.models import Document, Meeting
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

async def fetch_all_vexa_transcripts():
    """
    Fetch all pending Vexa transcripts and process them.
    """
    async with AsyncSessionLocal() as db:
        print("\n" + "="*80)
        print("FETCHING ALL VEXA TRANSCRIPTS")
        print("="*80 + "\n")
        
        # 1. Find all placeholder documents
        stmt = select(Document).where(Document.document_type == "transcript_placeholder")
        result = await db.execute(stmt)
        docs = result.scalars().all()
        
        if not docs:
            print("❌ No placeholder documents found.")
            return
        
        print(f"Found {len(docs)} placeholder documents to check:\n")
        
        success_count = 0
        failed_count = 0
        not_ready_count = 0
        
        for idx, doc in enumerate(docs, 1):
            session_id = doc.metadata_json.get("vexa_session_id")
            if not session_id:
                print(f"{idx}. Document {doc.id}: No session ID found, skipping")
                continue
            
            print(f"{idx}. Session {session_id} (Meeting: {doc.meeting_id})")
            print(f"   File: {doc.file_name}")
            
            # Try to fetch transcript
            transcript_url = f"{settings.VEXA_API_URL}/v1/sessions/{session_id}/transcript"
            headers = {
                "Authorization": f"Bearer {settings.VEXA_API_KEY}",
                "X-API-Key": settings.VEXA_API_KEY,
                "Content-Type": "application/json"
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(transcript_url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            transcript_text = data.get('text', data.get('transcript', ''))
                            
                            if not transcript_text:
                                # Try to get from other fields
                                transcript_text = str(data)
                            
                            print(f"   ✓ Transcript available! Length: {len(transcript_text)} chars")
                            
                            # Fetch meeting
                            stmt_m = select(Meeting).where(Meeting.id == doc.meeting_id)
                            res_m = await db.execute(stmt_m)
                            meeting = res_m.scalar_one_or_none()
                            
                            if meeting:
                                print(f"   Processing for meeting: {meeting.title}")
                                file_path = await vexa_service.process_transcript_text(meeting, transcript_text, db)
                                
                                if file_path:
                                    # Update document
                                    doc.document_type = "transcript"
                                    doc.file_type = "text/plain"
                                    doc.file_path = str(file_path)
                                    doc.metadata_json["status"] = "completed"
                                    
                                    await db.commit()
                                    print(f"   ✓ SUCCESS! Minutes generated and saved")
                                    success_count += 1
                                else:
                                    print(f"   ✗ Failed to process transcript")
                                    failed_count += 1
                            else:
                                print(f"   ✗ Meeting not found")
                                failed_count += 1
                                
                        elif resp.status == 404:
                            print(f"   ⏳ Transcript not ready yet (404)")
                            not_ready_count += 1
                        else:
                            error_text = await resp.text()
                            print(f"   ✗ Error {resp.status}: {error_text[:100]}")
                            failed_count += 1
                            
            except Exception as e:
                print(f"   ✗ Exception: {e}")
                failed_count += 1
            
            print()  # Blank line between entries
        
        # Summary
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"✓ Successfully processed: {success_count}")
        print(f"⏳ Not ready yet:         {not_ready_count}")
        print(f"✗ Failed:                {failed_count}")
        print(f"📊 Total checked:         {len(docs)}")
        print()

if __name__ == "__main__":
    asyncio.run(fetch_all_vexa_transcripts())
