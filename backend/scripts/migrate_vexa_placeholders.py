"""
Migrate existing Vexa placeholder documents to include platform and native_meeting_id.
"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.models import Document, Meeting

async def migrate_vexa_placeholders():
    async with AsyncSessionLocal() as db:
        print("Migrating Vexa placeholder documents...")
        
        # Find all placeholder documents
        stmt = select(Document).where(Document.document_type == "transcript_placeholder")
        result = await db.execute(stmt)
        docs = result.scalars().all()
        
        print(f"Found {len(docs)} placeholder documents")
        
        updated_count = 0
        for doc in docs:
            # Check if already has platform and native_meeting_id
            if doc.metadata_json.get("platform") and doc.metadata_json.get("native_meeting_id"):
                print(f"  Document {doc.id} already migrated, skipping")
                continue
            
            # Fetch the meeting to get the video_link or location
            stmt_m = select(Meeting).where(Meeting.id == doc.meeting_id)
            res_m = await db.execute(stmt_m)
            meeting = res_m.scalar_one_or_none()
            
            if not meeting:
                print(f"  Document {doc.id}: Meeting not found, skipping")
                continue
            
            # Extract platform and native_meeting_id from meeting URL
            meet_url = None
            if meeting.location and "meet.google.com" in meeting.location:
                meet_url = meeting.location
            elif meeting.video_link and "meet.google.com" in meeting.video_link:
                meet_url = meeting.video_link
            
            if not meet_url:
                print(f"  Document {doc.id}: No Google Meet URL found, skipping")
                continue
            
            # Parse URL
            platform = "google_meet"
            native_meeting_id = meet_url.split("/")[-1].split("?")[0]
            
            # Update metadata
            doc.metadata_json["platform"] = platform
            doc.metadata_json["native_meeting_id"] = native_meeting_id
            
            print(f"  ✓ Updated document {doc.id}: {platform}/{native_meeting_id}")
            updated_count += 1
        
        await db.commit()
        print(f"\nMigration complete! Updated {updated_count} documents")

if __name__ == "__main__":
    asyncio.run(migrate_vexa_placeholders())
