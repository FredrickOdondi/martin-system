import asyncio
from sqlalchemy import text
from app.core.database import engine

async def apply_cascade_fixes():
    queries = [
        # Drop existing constraints if they exist (Postgres specific)
        "ALTER TABLE twg_members DROP CONSTRAINT IF EXISTS twg_members_user_id_fkey",
        "ALTER TABLE twg_members ADD CONSTRAINT twg_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
        
        "ALTER TABLE meeting_participants DROP CONSTRAINT IF EXISTS meeting_participants_user_id_fkey",
        "ALTER TABLE meeting_participants ADD CONSTRAINT meeting_participants_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE",
        
        "ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey",
        "ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL",
        
        "ALTER TABLE twgs DROP CONSTRAINT IF EXISTS twgs_political_lead_id_fkey",
        "ALTER TABLE twgs ADD CONSTRAINT twgs_political_lead_id_fkey FOREIGN KEY (political_lead_id) REFERENCES users(id) ON DELETE SET NULL",
        
        "ALTER TABLE twgs DROP CONSTRAINT IF EXISTS twgs_technical_lead_id_fkey",
        "ALTER TABLE twgs ADD CONSTRAINT twgs_technical_lead_id_fkey FOREIGN KEY (technical_lead_id) REFERENCES users(id) ON DELETE SET NULL",
        
        "ALTER TABLE action_items DROP CONSTRAINT IF EXISTS action_items_owner_id_fkey",
        "ALTER TABLE action_items ADD CONSTRAINT action_items_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE",
        
        "ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_uploaded_by_id_fkey",
        "ALTER TABLE documents ADD CONSTRAINT documents_uploaded_by_id_fkey FOREIGN KEY (uploaded_by_id) REFERENCES users(id) ON DELETE CASCADE"
    ]
    
    async with engine.begin() as conn:
        for q in queries:
            try:
                await conn.execute(text(q))
                print(f"Executed: {q}")
            except Exception as e:
                print(f"Failed: {q} - {e}")

if __name__ == "__main__":
    asyncio.run(apply_cascade_fixes())
