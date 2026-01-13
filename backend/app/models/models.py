import uuid
import enum
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import String, DateTime, Enum, ForeignKey, Column, Table, Text, Numeric, Float, Boolean, JSON, Uuid, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from app.core.database import Base
except ImportError:
    from app.core.database import Base

# --- Enums ---

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TWG_FACILITATOR = "twg_facilitator"
    TWG_MEMBER = "twg_member"
    SECRETARIAT_LEAD = "secretariat_lead"

class TWGPillar(str, enum.Enum):
    energy_infrastructure = "energy_infrastructure"
    agriculture_food_systems = "agriculture_food_systems"
    critical_minerals_industrialization = "critical_minerals_industrialization"
    digital_economy_transformation = "digital_economy_transformation"
    protocol_logistics = "protocol_logistics"
    resource_mobilization = "resource_mobilization"

class MeetingStatus(str, enum.Enum):
    REQUESTED = "requested"  # New: Pending Supervisor approval
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class RsvpStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

class MinutesStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    REVIEW = "review"
    APPROVED = "approved"
    FINAL = "final"

class ActionItemStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"

class ActionItemPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ProjectStatus(str, enum.Enum):
    IDENTIFIED = "identified"
    VETTING = "vetting"
    BANKABLE = "bankable"
    PRESENTED = "presented"

class NotificationType(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ALERT = "alert"
    MESSAGE = "message"
    DOCUMENT = "document"
    TASK = "task"

class ConflictType(str, enum.Enum):
    SCHEDULE_CLASH = "schedule_clash"
    RESOURCE_CONSTRAINT = "resource_constraint"
    POLICY_MISALIGNMENT = "policy_misalignment"
    DEPENDENCY_BLOCKER = "dependency_blocker"
    VIP_AVAILABILITY = "vip_availability" # New

class ConflictSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ConflictStatus(str, enum.Enum):
    DETECTED = "detected"
    NEGOTIATING = "negotiating"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class DependencyStatus(str, enum.Enum):
    PENDING = "pending"
    SATISFIED = "satisfied"
    BLOCKED = "blocked"

# --- Association Tables ---

twg_members = Table(
    "twg_members",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("twg_id", Uuid, ForeignKey("twgs.id", ondelete="CASCADE"), primary_key=True),
    Column("joined_at", DateTime, default=datetime.utcnow),
    extend_existing=True
)

# MeetingParticipant Class (Association Object)
class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    meeting_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("meetings.id", ondelete="CASCADE"))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    rsvp_status: Mapped[RsvpStatus] = mapped_column(Enum(RsvpStatus), default=RsvpStatus.PENDING)
    attended: Mapped[bool] = mapped_column(Boolean, default=False)
    
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    meeting: Mapped["Meeting"] = relationship(back_populates="participants")
    user: Mapped[Optional["User"]] = relationship(back_populates="meeting_participations")

# --- Models ---

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.TWG_MEMBER)
    organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    twgs: Mapped[List["TWG"]] = relationship(
        secondary=twg_members, back_populates="members"
    )

    @property
    def twg_ids(self) -> List[uuid.UUID]:
        return [twg.id for twg in self.twgs]
    
    owned_action_items: Mapped[List["ActionItem"]] = relationship(back_populates="owner")
    meeting_participations: Mapped[List["MeetingParticipant"]] = relationship(back_populates="user")
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", order_by="Notification.created_at.desc()"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")
    
    # VIP Profile (One-to-One)
    vip_profile: Mapped[Optional["VipProfile"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")

class VipProfile(Base):
    """
    Profile for Very Important Persons (Ministers, Heads of State, etc.)
    Tracks their priority level and availability constraints.
    """
    __tablename__ = "vip_profiles"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    title: Mapped[str] = mapped_column(String(100)) # e.g. "Minister of Energy"
    priority_level: Mapped[int] = mapped_column(Integer, default=1) # 1=Standard, 5=Head of State
    companies: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Companies/Orgs they represent
    
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # e.g. "No morning meetings"
    calendar_sync_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="vip_profile")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(255))
    resource_type: Mapped[str] = mapped_column(String(100)) # e.g., "meeting", "document", "project"
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # Contextual info
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")

class TWG(Base):
    __tablename__ = "twgs"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    pillar: Mapped[TWGPillar] = mapped_column(Enum(TWGPillar))
    status: Mapped[str] = mapped_column(String(50), default="active")
    
    political_lead_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    technical_lead_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    political_lead: Mapped[Optional["User"]] = relationship("User", foreign_keys=[political_lead_id])
    technical_lead: Mapped[Optional["User"]] = relationship("User", foreign_keys=[technical_lead_id])

    members: Mapped[List["User"]] = relationship(
        secondary=twg_members, back_populates="twgs"
    )
    meetings: Mapped[List["Meeting"]] = relationship(back_populates="twg")
    projects: Mapped[List["Project"]] = relationship(back_populates="twg")
    action_items: Mapped[List["ActionItem"]] = relationship(back_populates="twg")
    documents: Mapped[List["Document"]] = relationship(back_populates="twg")
    
    # Dependencies
    dependencies_as_source: Mapped[List["Dependency"]] = relationship("Dependency", foreign_keys="[Dependency.source_twg_id]", back_populates="source_twg")
    dependencies_as_target: Mapped[List["Dependency"]] = relationship("Dependency", foreign_keys="[Dependency.target_twg_id]", back_populates="target_twg")

class Dependency(Base):
    """
    Tracks cross-TWG dependencies.
    Example: Minerals TWG (source) must decide on 'smelting_policy' 
    before Energy TWG (target) can schedule 'power_planning'
    """
    __tablename__ = "dependencies"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    
    source_twg_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("twgs.id"))
    target_twg_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("twgs.id"))
    
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[DependencyStatus] = mapped_column(Enum(DependencyStatus), default=DependencyStatus.PENDING)
    
    # Optional links to blocking artifacts
    blocking_meeting_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("meetings.id"), nullable=True)
    blocking_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("documents.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    source_twg: Mapped["TWG"] = relationship("TWG", foreign_keys=[source_twg_id], back_populates="dependencies_as_source")
    target_twg: Mapped["TWG"] = relationship("TWG", foreign_keys=[target_twg_id], back_populates="dependencies_as_target")
    blocking_meeting: Mapped[Optional["Meeting"]] = relationship("Meeting")
    blocking_document: Mapped[Optional["Document"]] = relationship("Document")

class Meeting(Base):
    __tablename__ = "meetings"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    twg_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("twgs.id"))
    title: Mapped[str] = mapped_column(String(255))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(default=60)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[MeetingStatus] = mapped_column(Enum(MeetingStatus), default=MeetingStatus.SCHEDULED)
    meeting_type: Mapped[str] = mapped_column(String(50), default="virtual") # virtual, in-person
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Text or link to transcript
    video_link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True) # Google Meet / Zoom link
    
    # Relationships
    twg: Mapped["TWG"] = relationship(back_populates="meetings")
    participants: Mapped[List["MeetingParticipant"]] = relationship(
        "MeetingParticipant", back_populates="meeting", cascade="all, delete-orphan"
    )
    agenda: Mapped[Optional["Agenda"]] = relationship(back_populates="meeting", uselist=False)
    minutes: Mapped[Optional["Minutes"]] = relationship(back_populates="meeting", uselist=False)
    action_items: Mapped[List["ActionItem"]] = relationship(back_populates="meeting")
    documents: Mapped[List["Document"]] = relationship(back_populates="meeting")

class Agenda(Base):
    __tablename__ = "agendas"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    meeting_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("meetings.id"), unique=True)
    content: Mapped[str] = mapped_column(Text) # Markdown or HTML
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    meeting: Mapped["Meeting"] = relationship(back_populates="agenda")

class Minutes(Base):
    __tablename__ = "minutes"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    meeting_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("meetings.id"), unique=True)
    content: Mapped[str] = mapped_column(Text) # Markdown or HTML
    key_decisions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[MinutesStatus] = mapped_column(Enum(MinutesStatus, values_callable=lambda x: [e.value for e in x]), default=MinutesStatus.DRAFT)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    meeting: Mapped["Meeting"] = relationship(back_populates="minutes")

class ActionItem(Base):
    __tablename__ = "action_items"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    twg_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("twgs.id"))
    meeting_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("meetings.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    due_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[ActionItemStatus] = mapped_column(Enum(ActionItemStatus), default=ActionItemStatus.PENDING)
    priority: Mapped[ActionItemPriority] = mapped_column(Enum(ActionItemPriority), default=ActionItemPriority.MEDIUM)
    
    # Relationships
    twg: Mapped["TWG"] = relationship(back_populates="action_items")
    meeting: Mapped[Optional["Meeting"]] = relationship(back_populates="action_items")
    owner: Mapped["User"] = relationship(back_populates="owned_action_items")

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    twg_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("twgs.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    investment_size: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    readiness_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.IDENTIFIED)
    investment_memo_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("documents.id"), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    twg: Mapped["TWG"] = relationship(back_populates="projects")
    investment_memo: Mapped[Optional["Document"]] = relationship(foreign_keys=[investment_memo_id])

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    twg_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("twgs.id"), nullable=True)
    meeting_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("meetings.id"), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(512))
    file_type: Mapped[str] = mapped_column(String(255))  # MIME type can be long
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    twg: Mapped[Optional["TWG"]] = relationship(back_populates="documents")
    meeting: Mapped[Optional["Meeting"]] = relationship(back_populates="documents")

    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Knowledge Broadcasting
    scope: Mapped[List[str]] = mapped_column(JSON, default=["twg_restricted"]) 
    category: Mapped[str] = mapped_column(String(50), default="twg_specific")
    last_broadcast: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    access_control: Mapped[str] = mapped_column(String(50), default="twg_restricted")
    parent_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("documents.id"), nullable=True)

    # Relationships
    parent_document: Mapped[Optional["Document"]] = relationship("Document", remote_side="Document.id", back_populates="versions")
    versions: Mapped[List["Document"]] = relationship("Document", back_populates="parent_document", cascade="all, delete-orphan")

    uploaded_by: Mapped["User"] = relationship("User", foreign_keys=[uploaded_by_id])

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), default=NotificationType.INFO)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="notifications")

class Conflict(Base):
    __tablename__ = "conflicts"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conflict_type: Mapped[ConflictType] = mapped_column(Enum(ConflictType))
    severity: Mapped[ConflictSeverity] = mapped_column(Enum(ConflictSeverity))
    description: Mapped[str] = mapped_column(Text)
    agents_involved: Mapped[List[str]] = mapped_column(JSON) # List of agent names
    conflicting_positions: Mapped[dict] = mapped_column(JSON) # Key: agent name, Value: position description
    
    status: Mapped[ConflictStatus] = mapped_column(Enum(ConflictStatus), default=ConflictStatus.DETECTED)
    resolution_log: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True) # History of negotiation
    human_action_required: Mapped[bool] = mapped_column(Boolean, default=False)
    
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class WeeklyPacket(Base):
    __tablename__ = "weekly_packets"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    twg_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("twgs.id"))
    week_start_date: Mapped[datetime] = mapped_column(DateTime)
    
    # Structured Data (stored as JSON)
    proposed_sessions: Mapped[List[dict]] = mapped_column(JSON) # List of proposed meetings
    dependencies: Mapped[List[dict]] = mapped_column(JSON) # Identified cross-TWG dependencies
    accomplishments: Mapped[List[str]] = mapped_column(JSON) # Bullet points of achievements
    risks_and_blockers: Mapped[List[dict]] = mapped_column(JSON) # Identified risks
    
    status: Mapped[str] = mapped_column(String(50), default="draft") # draft, submitted, ingested
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    twg: Mapped["TWG"] = relationship("TWG")
