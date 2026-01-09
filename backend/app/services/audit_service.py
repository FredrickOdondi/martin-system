from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AuditLog
from typing import Optional, Dict, Any
import uuid

class AuditService:
    async def log_activity(
        self,
        db: AsyncSession,
        user_id: Optional[uuid.UUID],
        action: str,
        resource_type: str,
        resource_id: Optional[uuid.UUID],
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ):
        """
        Records an action in the audit log.
        """
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address
        )
        db.add(audit_entry)
        # Note: Caller is responsible for commit, or we can flush here if needed immediately.
        # Usually best to let the main transaction commit, unless this is critical logging that must persist even if main tx fails (which requires separate tx).
        # For simplicity in this architecture, we attach to the current session.
        
audit_service = AuditService()
