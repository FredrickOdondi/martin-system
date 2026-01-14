"""
Pipeline Schemas

Pydantic models for the Deal Pipeline API.
"""
from pydantic import BaseModel, Field, condecimal
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from app.models.models import ProjectStatus, InvestorMatchStatus

class ProjectIngest(BaseModel):
    """Schema for ingesting a project proposal"""
    twg_id: str
    name: str
    description: str
    investment_size: Decimal
    currency: str = "USD"
    readiness_score: float = Field(..., ge=0, le=10)
    strategic_alignment_score: float = Field(..., ge=0, le=10)
    pillar: Optional[str] = None
    lead_country: Optional[str] = None
    assigned_agent: Optional[str] = None

class ProjectAdvanceStage(BaseModel):
    """Schema for advancing a project stage"""
    new_stage: ProjectStatus
    notes: Optional[str] = None

class InvestorMatchUpdate(BaseModel):
    """Schema for updating investor match status"""
    status: InvestorMatchStatus
    notes: Optional[str] = None


class InvestorRead(BaseModel):
    """Schema for investor details"""
    id: UUID
    name: str
    sector_preferences: Optional[List[str]] = None
    ticket_size_min: Optional[Decimal] = None
    ticket_size_max: Optional[Decimal] = None
    geographic_focus: Optional[List[str]] = None
    investment_instruments: Optional[List[str]] = None

class InvestorMatchRead(BaseModel):
    """Schema for investor match details"""
    match_id: str
    investor: InvestorRead
    score: float
    status: str
    notes: Optional[str] = None

class ProjectPipelineRead(BaseModel):
    """Schema for detailed project view in pipeline"""
    id: UUID
    name: str
    description: str
    status: ProjectStatus  # Changed from 'stage' to 'status'
    investment_size: Decimal
    currency: str = "USD"
    
    # Scores
    readiness_score: float = 0.0
    afcen_score: Optional[Decimal] = None
    strategic_alignment_score: Optional[Decimal] = None
    regional_impact_score: Optional[Decimal] = None
    
    # Metadata
    pillar: Optional[str] = None
    lead_country: Optional[str] = None
    assigned_agent: Optional[str] = None
    updated_at: datetime
    
    # Computed
    days_in_stage: Optional[int] = None
    is_stalled: bool = False

class PipelineStats(BaseModel):
    """Schema for pipeline dashboard stats"""
    total_projects: int
    healthy_projects: int
    stalled_projects: List[Any]
    by_stage: Dict[str, Any]
    checked_at: datetime
