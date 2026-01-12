from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter(tags=["Debug"])

@router.get("/debug/schema")
async def inspect_schema(db: AsyncSession = Depends(get_db)):
    """
    Inspects the actual database columns for 'twgs' and 'documents' tables.
    Returns a list of columns found in the database.
    """
    try:
        # Check TWGS columns
        twg_result = await db.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'twgs';"
        ))
        twg_columns = [{"name": row[0], "type": row[1]} for row in twg_result.fetchall()]

        # Check DOCUMENTS columns
        doc_result = await db.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'documents';"
        ))
        return {
            "twgs_columns": twg_columns,
            "documents_columns": doc_columns
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/test_twgs")
async def test_twgs(db: AsyncSession = Depends(get_db)):
    """Runs the exact query from list_twgs to capture the error."""
    try:
        from app.models.models import TWG
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        query_options = [
            selectinload(TWG.political_lead),
            selectinload(TWG.technical_lead),
        ]
        result = await db.execute(select(TWG).options(*query_options).limit(5))
        twgs = result.scalars().all()
        return {"status": "success", "count": len(twgs), "data": [{"name": t.name, "pillar": str(t.pillar)} for t in twgs]}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}

@router.get("/debug/test_documents")
async def test_documents(db: AsyncSession = Depends(get_db)):
    """Runs the exact query from list_documents to capture the error."""
    try:
        from app.models.models import Document
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(select(Document).limit(5))
        docs = result.scalars().all()
        return {"status": "success", "count": len(docs)}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}

