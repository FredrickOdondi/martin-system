"""
Supervisor State Schemas

Pydantic models for supervisor global state snapshots.
"""

from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.models import (
    MeetingStatus, ProjectStatus, TWGPillar, 
    ConflictStatus, ConflictSeverity
)


class MeetingSnapshot(BaseModel):
    """Snapshot of a meeting for global calendar"""
    id: UUID
    twg_id: UUID
    twg_name: str
    title: str
    scheduled_at: datetime
    duration_minutes: int
    location: Optional[str] = None
    status: MeetingStatus
    participant_count: int
    has_conflicts: bool = Field(
        default=False, 
        description="True if meeting has scheduling conflicts"
    )
    
    class Config:
        from_attributes = True


class DocumentSnapshot(BaseModel):
    """Snapshot of a document for registry"""
    id: UUID
    twg_id: Optional[UUID] = None
    twg_name: Optional[str] = None
    file_name: str
    file_type: str
    created_at: datetime
    is_confidential: bool
    uploaded_by_name: str
    version: int = 1
    has_newer_version: bool = False
    parent_document_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class ProjectSnapshot(BaseModel):
    """Snapshot of a project for pipeline view"""
    id: UUID
    twg_id: UUID
    twg_name: str
    name: str
    description: str
    investment_size: Decimal
    currency: str
    readiness_score: float
    status: ProjectStatus
    
    class Config:
        from_attributes = True


class ConflictSnapshot(BaseModel):
    """Snapshot of an active conflict"""
    id: UUID
    conflict_type: str
    severity: ConflictSeverity
    description: str
    agents_involved: List[str]
    status: ConflictStatus
    detected_at: datetime
    
    class Config:
        from_attributes = True


class DependencySnapshot(BaseModel):
    """Cross-TWG dependency"""
    id: UUID
    source_twg_id: UUID
    source_twg_name: str
    target_twg_id: UUID
    target_twg_name: str
    description: str
    status: str  # pending, acknowledged, resolved
    created_at: datetime


class TWGSummary(BaseModel):
    """Summary statistics for a single TWG"""
    twg_id: UUID
    twg_name: str
    pillar: TWGPillar
    status: str
    total_meetings: int
    upcoming_meetings: int
    completed_meetings: int
    total_documents: int
    total_projects: int
    active_conflicts: int
    last_activity: Optional[datetime] = None
    
    # Project pipeline breakdown
    projects_by_status: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of projects by status"
    )


class SupervisorStateSnapshot(BaseModel):
    """Complete global state snapshot"""
    
    # Core data
    calendar: List[MeetingSnapshot] = Field(
        description="All meetings across all TWGs"
    )
    documents: List[DocumentSnapshot] = Field(
        description="All documents in the system"
    )
    projects: List[ProjectSnapshot] = Field(
        description="All projects in pipeline"
    )
    
    # Aggregated views
    twg_summaries: Dict[str, TWGSummary] = Field(
        description="Per-TWG summary statistics"
    )
    active_conflicts: List[ConflictSnapshot] = Field(
        description="Currently active conflicts"
    )
    dependencies: List[DependencySnapshot] = Field(
        default_factory=list,
        description="Cross-TWG dependencies"
    )
    
    # Metadata
    last_refresh: datetime = Field(
        description="When state was last refreshed"
    )
    total_twgs: int
    total_meetings: int
    total_documents: int
    total_projects: int
    
    class Config:
        from_attributes = True


class GlobalCalendarResponse(BaseModel):
    """Response for unified calendar endpoint"""
    meetings: List[MeetingSnapshot]
    total_meetings: int
    upcoming_meetings: int
    conflicts_detected: int
    last_refresh: datetime


class DocumentRegistryResponse(BaseModel):
    """Response for document registry endpoint"""
    documents: List[DocumentSnapshot]
    total_documents: int
    by_twg: Dict[str, int]
    last_refresh: datetime


class ProjectPipelineResponse(BaseModel):
    """Response for project pipeline endpoint"""
    projects: List[ProjectSnapshot]
    total_projects: int
    by_status: Dict[str, int]
    by_twg: Dict[str, int]
    total_investment: Decimal
    last_refresh: datetime
