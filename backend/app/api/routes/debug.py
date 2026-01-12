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
        doc_columns = [{"name": row[0], "type": row[1]} for row in doc_result.fetchall()]

        return {
            "twgs_columns": twg_columns,
            "documents_columns": doc_columns
        }
    except Exception as e:
        return {"error": str(e)}
