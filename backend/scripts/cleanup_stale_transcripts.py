
import asyncio
from app.core.database import get_db_session_context
from app.models.models import Document
from sqlalchemy import select

async def cleanup_stale_docs():
    async with get_db_session_context() as db:
        # fetch all placeholders
        stmt = select(Document).where(Document.document_type == "transcript_placeholder")
        result = await db.execute(stmt)
        docs = result.scalars().all()
        
        count = 0
        for doc in docs:
            meta = doc.metadata_json or {}
            platform = meta.get("platform")
            native_id = meta.get("native_meeting_id")
            
            if not platform or not native_id:
                print(f"Deleting stale document {doc.id} (meta: {meta})")
                await db.delete(doc)
                count += 1
        
        if count > 0:
            await db.commit()
            print(f"Successfully deleted {count} stale documents.")
        else:
            print("No stale documents found.")

if __name__ == '__main__':
    asyncio.run(cleanup_stale_docs())
