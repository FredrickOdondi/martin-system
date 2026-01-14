from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from app.schemas.schemas import MeetingCreate, DependencyType, DependencySource

class DependencyDeclaration(BaseModel):
    """
    Agnets declare dependencies by referencing titles (since IDs might not exist yet).
    The system will attempt to resolve these to UUIDs during ingestion.
    """
    source_meeting_title: str # "The meeting that must finish first"
    target_meeting_title: str # "The meeting that depends on the source"
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    reason: Optional[str] = None

class TWGWeeklyPacket(BaseModel):
    twg_id: uuid.UUID
    week_start_date: datetime
    
    # The agent submits a list of planned meetings
    proposed_meetings: List[MeetingCreate]
    
    # The agent declares dependencies (internal or cross-TWG)
    dependencies: List[DependencyDeclaration] = []
    
    accomplishments: List[str] = []
    risks_and_blockers: List[dict] = []
