from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_
from typing import List, Dict, Any, Optional
import datetime
import io
import csv

from app.core.database import get_db
from app.models.models import User, Meeting, ActionItem, Document, TWG, Project, MeetingStatus, ActionItemStatus, ProjectStatus
from app.api.deps import get_current_active_user
from sqlalchemy.orm import selectinload
from app.core.ws_manager import ws_manager
from app.utils.security import verify_token

from app.schemas.schemas import ConflictRead

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# ... (existing code)

@router.get("/conflicts", response_model=List[ConflictRead])
async def get_conflicts(
    include_history: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get current conflicts/inconsistencies detected by the Supervisor.
    If include_history is True, also returns RESOLVED and DISMISSED conflicts.
    """
    from app.models.models import Conflict, ConflictStatus
    
    query = select(Conflict).order_by(desc(Conflict.detected_at))
    
    if not include_history:
        query = query.where(Conflict.status != ConflictStatus.RESOLVED)\
                     .where(Conflict.status != ConflictStatus.DISMISSED)
    
    result = await db.execute(query)
    conflicts = result.scalars().all()
    return conflicts

@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get aggregated statistics for the Command Center dashboard.
    """
    # Scope by TWG if not admin
    from app.models.models import UserRole
    is_admin = current_user.role == UserRole.ADMIN
    user_twg_ids = [t.id for t in current_user.twgs] if not is_admin else []

    # 1. Meeting Stats
    q_total = select(func.count(Meeting.id))
    q_completed = select(func.count(Meeting.id)).where(Meeting.status == MeetingStatus.COMPLETED)
    q_upcoming = select(func.count(Meeting.id)).where(Meeting.status == MeetingStatus.SCHEDULED)
    
    if not is_admin:
        q_total = q_total.where(Meeting.twg_id.in_(user_twg_ids))
        q_completed = q_completed.where(Meeting.twg_id.in_(user_twg_ids))
        q_upcoming = q_upcoming.where(Meeting.twg_id.in_(user_twg_ids))
        
    total_meetings_res = await db.execute(q_total)
    total_meetings = total_meetings_res.scalar() or 0
    
    completed_res = await db.execute(q_completed)
    completed_meetings = completed_res.scalar() or 0
    
    upcoming_res = await db.execute(q_upcoming)
    upcoming_meetings = upcoming_res.scalar() or 0
    
    # Next Plenary Calculation (Global Event, maybe visible to all? Spec says "cross-TWG outputs" restricted. 
    # But Plenary is usually for everyone. Let's start restricted.)
    q_plenary = select(Meeting).where(
            Meeting.status == MeetingStatus.SCHEDULED,
            or_(Meeting.title.ilike("%plenary%"), Meeting.title.ilike("%summit%"))
        ).order_by(Meeting.scheduled_at).limit(1)
        
    next_plenary_res = await db.execute(q_plenary)
    next_plenary = next_plenary_res.scalar_one_or_none()
    
    # 2. Action Item Stats
    q_items = select(func.count(ActionItem.id))
    q_items_comp = select(func.count(ActionItem.id)).where(ActionItem.status == ActionItemStatus.COMPLETED)
    q_items_pend = select(func.count(ActionItem.id)).where(ActionItem.status == ActionItemStatus.PENDING)
    
    if not is_admin:
        # Action Items linked to Meetings linked to TWGs
        # Or ActionItems have twg_id? Let's check model. 
        # ActionItem has meeting_id. Meeting has twg_id.
        # This requires a join.
        q_items = q_items.join(Meeting).where(Meeting.twg_id.in_(user_twg_ids))
        q_items_comp = q_items_comp.join(Meeting).where(Meeting.twg_id.in_(user_twg_ids))
        q_items_pend = q_items_pend.join(Meeting).where(Meeting.twg_id.in_(user_twg_ids))

    total_items_res = await db.execute(q_items)
    total_items = total_items_res.scalar() or 0
    
    completed_items_res = await db.execute(q_items_comp)
    completed_items = completed_items_res.scalar() or 0
    
    pending_approvals_res = await db.execute(q_items_pend)
    pending_approvals = pending_approvals_res.scalar() or 0
    
    # 3. Project / Pipeline Stats
    q_projects = select(Project)
    if not is_admin:
        q_projects = q_projects.where(Project.twg_id.in_(user_twg_ids))
        
    projects_res = await db.execute(q_projects)
    projects = projects_res.scalars().all()
    
    pipeline_stats = {
        "drafting": len([p for p in projects if p.status == ProjectStatus.IDENTIFIED]),
        "negotiation": len([p for p in projects if p.status == ProjectStatus.VETTING]),
        "final_review": len([p for p in projects if p.status == ProjectStatus.BANKABLE]),
        "signed": len([p for p in projects if p.status == ProjectStatus.PRESENTED]),
        "total": len(projects)
    }
    
    # 4. TWG Summary
    q_twgs = select(TWG).options(
            selectinload(TWG.projects),
            selectinload(TWG.meetings)
        )
    
    if not is_admin:
        q_twgs = q_twgs.where(TWG.id.in_(user_twg_ids))
        
    twgs_res = await db.execute(q_twgs)
    twgs = twgs_res.scalars().all()
    twg_stats = []
    
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=14)
    
    for twg in twgs:
        # Get Lead Name (fetching technical lead for lead name)
        lead_name = "System"
        if twg.technical_lead_id:
            lead_res = await db.execute(select(User).where(User.id == twg.technical_lead_id))
            lead = lead_res.scalar_one_or_none()
            if lead:
                lead_name = lead.full_name

        # Calculate Completion Percentage based on projects
        completion = 0
        if twg.projects:
            # Simple weighted average or count based on status
            done_projects = len([p for p in twg.projects if p.status == ProjectStatus.PRESENTED])
            completion = int((done_projects / len(twg.projects)) * 100) if twg.projects else 0
        
        # Check for activity (last meeting)
        last_meeting = None
        if twg.meetings:
            comp_meetings = [m for m in twg.meetings if m.status == MeetingStatus.COMPLETED]
            if comp_meetings:
                last_meeting = max(comp_meetings, key=lambda x: x.scheduled_at)
        
        is_stalled = False
        if last_meeting and last_meeting.scheduled_at < cutoff_date:
            is_stalled = True
        elif not last_meeting:
            future_meetings = [m for m in twg.meetings if m.status == MeetingStatus.SCHEDULED]
            if not future_meetings:
                 is_stalled = True
            
        twg_stats.append({
            "id": str(twg.id),
            "name": twg.name,
            "lead": lead_name,
            "status": "stalled" if is_stalled else "active",
            "completion": completion,
            "pillar": twg.pillar
        })
        
    return {
        "metrics": {
            "active_twgs": len([t for t in twg_stats if t["status"] == "active"]),
            "deals_in_pipeline": pipeline_stats["total"],
            "pending_approvals": pending_approvals,
            "next_plenary": {
                "date": next_plenary.scheduled_at if next_plenary else None,
                "title": next_plenary.title if next_plenary else "TBD"
            }
        },
        "pipeline": pipeline_stats,
        "twg_health": twg_stats
    }

@router.get("/timeline", response_model=List[Dict[str, Any]])
async def get_global_timeline(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get a unified timeline of recent and upcoming events.
    """
    # Fetch upcoming meetings and project deadlines
    # Fetch upcoming meetings and project deadlines
    from app.models.models import UserRole
    is_admin = current_user.role == UserRole.ADMIN
    user_twg_ids = [t.id for t in current_user.twgs] if not is_admin else []
    
    q_meetings = select(Meeting).options(selectinload(Meeting.twg)).where(Meeting.scheduled_at >= datetime.datetime.utcnow())
    if not is_admin:
        q_meetings = q_meetings.where(Meeting.twg_id.in_(user_twg_ids))
        
    meetings_res = await db.execute(
        q_meetings.order_by(Meeting.scheduled_at).limit(limit)
    )
    meetings = meetings_res.scalars().all()
    
    timeline = []
    for m in meetings:
        timeline.append({
            "type": "meeting",
            "date": m.scheduled_at,
            "title": m.title,
            "twg": m.twg.name if m.twg else "General",
            "status": "critical" if "plenary" in m.title.lower() or "summit" in m.title.lower() else "normal"
        })
        
    # Add some mock deadlines for now if none exist to make it look "real time"
    # In a real app, we'd fetch from ActionItems or Project metadata
    if not timeline:
        timeline.append({
            "type": "deadline",
            "date": datetime.datetime.utcnow() + datetime.timedelta(days=2),
            "title": "Draft Submission Deadline",
            "twg": "Trade & Customs",
            "status": "critical"
        })

    return timeline[:limit]

@router.get("/export")
async def export_dashboard_report(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Export a CSV report of the dashboard metrics and TWG status.
    """
    # Reuse the logic from get_dashboard_stats to get current data
    stats = await get_dashboard_stats(db, current_user)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write Header
    writer.writerow(["Summit Intelligence Report", datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])
    
    # Global Metrics
    writer.writerow(["GLOBAL METRICS"])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Active TWGs", stats["metrics"]["active_twgs"]])
    writer.writerow(["Deals in Pipeline", stats["metrics"]["deals_in_pipeline"]])
    writer.writerow(["Pending Tasks", stats["metrics"]["pending_approvals"]])
    writer.writerow(["Next Major Event", stats["metrics"]["next_plenary"]["title"]])
    writer.writerow(["Next Event Date", stats["metrics"]["next_plenary"]["date"]])
    writer.writerow([])
    
    # Pipeline Stats
    writer.writerow(["PIPELINE STATUS"])
    writer.writerow(["Stage", "Count"])
    writer.writerow(["Drafting", stats["pipeline"]["drafting"]])
    writer.writerow(["Negotiation", stats["pipeline"]["negotiation"]])
    writer.writerow(["Final Review", stats["pipeline"]["final_review"]])
    writer.writerow(["Signed", stats["pipeline"]["signed"]])
    writer.writerow(["Total", stats["pipeline"]["total"]])
    writer.writerow([])
    
    # TWG Specifics
    writer.writerow(["TWG STATUS DETAILS"])
    writer.writerow(["ID", "Name", "Lead", "Status", "Completion %", "Pillar"])
    for twg in stats["twg_health"]:
        writer.writerow([
            twg["id"],
            twg["name"],
            twg["lead"],
            twg["status"],
            twg["completion"],
            twg["pillar"]
        ])
    
    output.seek(0)
    
    filename = f"summit_intelligence_report_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: str,
    resolution: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Resolve a conflict manually.
    """
    from app.models.models import Conflict, ConflictStatus
    import uuid
    
    result = await db.execute(select(Conflict).where(Conflict.id == uuid.UUID(conflict_id)))
    conflict = result.scalar_one_or_none()
    
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
        
    conflict.status = ConflictStatus.RESOLVED
    conflict.resolution_log = (conflict.resolution_log or []) + [{"action": "resolved_by_user", "user": current_user.email, "resolution": resolution, "timestamp": datetime.datetime.utcnow().isoformat()}]
    conflict.resolved_at = datetime.datetime.utcnow()
    
    await db.commit()
    await db.refresh(conflict)
    
    # Notify connected clients via WebSocket
    await ws_manager.broadcast({"type": "conflict_resolved", "id": str(conflict.id)})
    
    return conflict


@router.post("/conflicts/{conflict_id}/propose-resolution")
async def propose_conflict_resolution(
    conflict_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    The Mediator Role: Get AI-proposed resolutions for a conflict.
    Part of the "Debate Pattern" where agents negotiate before human intervention.
    """
    from app.models.models import Conflict, UserRole
    from app.services.reconciliation_service import get_reconciliation_service
    import uuid
    
    is_admin = current_user.role == UserRole.ADMIN
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can propose resolutions")
    
    result = await db.execute(select(Conflict).where(Conflict.id == uuid.UUID(conflict_id)))
    conflict = result.scalar_one_or_none()
    
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    service = get_reconciliation_service(db)
    proposals = await service.propose_resolution(conflict)
    
    return proposals


@router.post("/conflicts/{conflict_id}/auto-negotiate")
async def auto_negotiate_conflict(
    conflict_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Trigger automated agent negotiation for a conflict.
    The Supervisor attempts to resolve the conflict through the "Debate Pattern".
    
    High-confidence resolutions may be auto-applied.
    Low-confidence resolutions are flagged for human review.
    """
    from app.models.models import Conflict, UserRole
    from app.services.reconciliation_service import get_reconciliation_service
    import uuid
    
    is_admin = current_user.role == UserRole.ADMIN
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can trigger auto-negotiation")
    
    result = await db.execute(select(Conflict).where(Conflict.id == uuid.UUID(conflict_id)))
    conflict = result.scalar_one_or_none()
    
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    service = get_reconciliation_service(db)
    negotiation_result = await service.run_automated_negotiation(conflict)
    
    # Broadcast result
    await ws_manager.broadcast({
        "type": "negotiation_complete",
        "conflict_id": conflict_id,
        "result": negotiation_result["negotiation_result"]
    })
    
    return negotiation_result

@router.post("/weekly-packet")
async def generate_weekly_packet(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Generate a weekly summary packet of all TWG activities.
    Target: Friday 17:00 weekly briefing.
    """
    from app.models.models import UserRole, Conflict, ConflictStatus
    
    is_admin = current_user.role == UserRole.ADMIN
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can generate weekly packet")
    
    # Calculate week boundaries
    today = datetime.datetime.utcnow()
    week_start = today - datetime.timedelta(days=today.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + datetime.timedelta(days=7)
    
    # 1. Meetings this week
    meetings_res = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.twg))
        .where(
            Meeting.scheduled_at >= week_start,
            Meeting.scheduled_at < week_end
        )
    )
    meetings = meetings_res.scalars().all()
    
    # 2. Action Items created/completed this week
    actions_res = await db.execute(
        select(ActionItem)
        .where(ActionItem.due_date >= week_start, ActionItem.due_date < week_end)
    )
    actions = actions_res.scalars().all()
    
    # 3. Conflicts resolved this week
    conflicts_res = await db.execute(
        select(Conflict)
        .where(
            Conflict.resolved_at >= week_start,
            Conflict.resolved_at < week_end
        )
    )
    resolved_conflicts = conflicts_res.scalars().all()
    
    # 4. Pending conflicts
    pending_res = await db.execute(
        select(func.count(Conflict.id))
        .where(Conflict.status == ConflictStatus.PENDING)
    )
    pending_conflicts = pending_res.scalar() or 0
    
    # 5. TWG activity summary
    twgs_res = await db.execute(select(TWG))
    twgs = twgs_res.scalars().all()
    
    twg_summaries = []
    for twg in twgs:
        twg_meetings = [m for m in meetings if m.twg_id == twg.id]
        twg_actions = [a for a in actions if a.twg_id == twg.id]
        twg_summaries.append({
            "twg_id": str(twg.id),
            "name": twg.name,
            "pillar": twg.pillar.value if twg.pillar else "unknown",
            "meetings_this_week": len(twg_meetings),
            "actions_due": len(twg_actions),
            "status": "active" if twg_meetings else "quiet"
        })
    
    return {
        "packet_date": today.isoformat(),
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "summary": {
            "total_meetings": len(meetings),
            "completed_meetings": len([m for m in meetings if m.status == MeetingStatus.COMPLETED]),
            "scheduled_meetings": len([m for m in meetings if m.status == MeetingStatus.SCHEDULED]),
            "action_items_due": len(actions),
            "action_items_completed": len([a for a in actions if a.status == ActionItemStatus.COMPLETED]),
            "conflicts_resolved": len(resolved_conflicts),
            "conflicts_pending": pending_conflicts
        },
        "twg_activity": twg_summaries,
        "status": "generated"
    }


@router.post("/force-reconciliation")
async def force_reconciliation(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Force the Supervisor Agent to scan all TWGs for conflicts and inconsistencies.
    This is the "Air Traffic Controller" for the summit - detecting collision courses
    before they happen.
    
    Checks:
    1. VIP Double-bookings (same person in overlapping meetings)
    2. Same-slot conflicts (multiple meetings at exact same time)
    3. Venue conflicts (same location at overlapping times)
    4. Time-slot crowding (3+ meetings in same hour = VIP bandwidth issue)
    5. Overdue action items (7+ days past due)
    """
    from app.models.models import UserRole, Conflict, ConflictStatus, ConflictType, ConflictSeverity
    import uuid
    from collections import defaultdict
    
    is_admin = current_user.role == UserRole.ADMIN
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can force reconciliation")
    
    detected_conflicts = []
    auto_resolved = []
    
    # Fetch all upcoming scheduled meetings
    upcoming_meetings = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.participants), selectinload(Meeting.twg))
        .where(Meeting.status == MeetingStatus.SCHEDULED)
        .where(Meeting.scheduled_at >= datetime.datetime.utcnow())
    )
    meetings = upcoming_meetings.scalars().all()
    
    # Fetch ALL existing conflicts to correctly handle resolved ones
    existing_conflicts_res = await db.execute(select(Conflict))
    existing_conflicts = existing_conflicts_res.scalars().all()
    
    active_descriptions = {
        c.description for c in existing_conflicts 
        if c.status in [ConflictStatus.DETECTED, ConflictStatus.NEGOTIATING, ConflictStatus.ESCALATED]
    }
    resolved_descriptions = {
        c.description for c in existing_conflicts 
        if c.status in [ConflictStatus.RESOLVED, ConflictStatus.DISMISSED]
    }
    
    def is_new_conflict(desc: str) -> bool:
        """True if conflict is completely new (not active AND not resolved)."""
        return desc not in active_descriptions and desc not in resolved_descriptions

    def is_active_conflict(desc: str) -> bool:
        """True if conflict already exists and is active."""
        return desc in active_descriptions
    
    # ===== 1. SAME-SLOT DETECTION =====
    # Group meetings by exact start time
    time_slots = defaultdict(list)
    for m in meetings:
        slot_key = m.scheduled_at.strftime('%Y-%m-%d %H:%M')
        time_slots[slot_key].append(m)
    
    for slot, slot_meetings in time_slots.items():
        if len(slot_meetings) >= 2:
            meeting_titles = [f"'{m.title}'" for m in slot_meetings]
            conflict_desc = f"⏰ Same-slot conflict: {len(slot_meetings)} meetings at {slot}: {', '.join(meeting_titles)}"
            # Logic:
            # 1. If it's a NEW conflict, create it and add to report.
            # 2. If it's an EXISTING ACTIVE conflict, just add to report (don't create).
            # 3. If it's a RESOLVED conflict, IGNORE it completely (don't report, don't create).
            
            if is_active_conflict(conflict_desc) or is_new_conflict(conflict_desc):
                # Only report if it's active or new (skip resolved)
                detected_conflicts.append({
                    "type": "same_slot",
                    "severity": "high",
                    "description": conflict_desc,
                    "affected_meetings": [str(m.id) for m in slot_meetings],
                    "slot": slot
                })
            
            # Create conflict record only if it's completely new
            if is_new_conflict(conflict_desc):
                new_conflict = Conflict(
                    id=uuid.uuid4(),
                    conflict_type=ConflictType.SCHEDULE_CLASH,
                    description=conflict_desc,
                    severity=ConflictSeverity.HIGH,
                    status=ConflictStatus.DETECTED,
                    agents_involved=[m.twg.name if m.twg else "Unknown" for m in slot_meetings],
                    conflicting_positions={m.title: f"Scheduled at {slot}" for m in slot_meetings},
                    detected_at=datetime.datetime.utcnow()
                )
                db.add(new_conflict)
                # Add to local set so we don't create it twice in same logic loop if weirdness happens
                active_descriptions.add(conflict_desc)
    
    # ===== 2. VENUE CONFLICTS =====
    # Group meetings by location  
    venue_schedule = defaultdict(list)
    for m in meetings:
        if m.location:
            venue_schedule[m.location.lower().strip()].append({
                "meeting_id": str(m.id),
                "title": m.title,
                "start": m.scheduled_at,
                "end": m.scheduled_at + datetime.timedelta(minutes=m.duration_minutes),
                "twg_id": str(m.twg_id) if m.twg_id else None
            })
    
    for venue, bookings in venue_schedule.items():
        for i, b1 in enumerate(bookings):
            for b2 in bookings[i+1:]:
                # Check overlap
                if b1["start"] < b2["end"] and b2["start"] < b1["end"]:
                    conflict_desc = f"🏛️ Venue conflict: '{venue}' double-booked for '{b1['title']}' and '{b2['title']}'"
                    
                    if is_active_conflict(conflict_desc) or is_new_conflict(conflict_desc):
                        detected_conflicts.append({
                            "type": "venue",
                            "severity": "high",
                            "description": conflict_desc,
                            "affected_meetings": [b1["meeting_id"], b2["meeting_id"]],
                            "venue": venue
                        })
                    
                    if is_new_conflict(conflict_desc):
                        new_conflict = Conflict(
                            id=uuid.uuid4(),
                            conflict_type=ConflictType.RESOURCE_CONSTRAINT,
                            description=conflict_desc,
                            severity=ConflictSeverity.HIGH,
                            status=ConflictStatus.DETECTED,
                            agents_involved=[b1["twg_id"] or "Unknown", b2["twg_id"] or "Unknown"],
                            conflicting_positions={b1["title"]: venue, b2["title"]: venue},
                            detected_at=datetime.datetime.utcnow()
                        )
                        db.add(new_conflict)
                        active_descriptions.add(conflict_desc)
    
    # ===== 3. VIP DOUBLE-BOOKINGS =====
    participant_schedule = defaultdict(list)
    for meeting in meetings:
        for p in meeting.participants:
            participant_schedule[p.email].append({
                "meeting_id": str(meeting.id),
                "title": meeting.title,
                "start": meeting.scheduled_at,
                "end": meeting.scheduled_at + datetime.timedelta(minutes=meeting.duration_minutes)
            })
    
    for email, bookings in participant_schedule.items():
        for i, b1 in enumerate(bookings):
            for b2 in bookings[i+1:]:
                if b1["start"] < b2["end"] and b2["start"] < b1["end"]:
                    conflict_desc = f"👤 VIP double-booked: {email} in '{b1['title']}' and '{b2['title']}'"
                    
                    if is_active_conflict(conflict_desc) or is_new_conflict(conflict_desc):
                        detected_conflicts.append({
                            "type": "vip_double_booking",
                            "severity": "high",
                            "description": conflict_desc,
                            "affected_meetings": [b1["meeting_id"], b2["meeting_id"]],
                            "participant": email
                        })
                    
                    if is_new_conflict(conflict_desc):
                        new_conflict = Conflict(
                            id=uuid.uuid4(),
                            conflict_type=ConflictType.SCHEDULE_CLASH,
                            description=conflict_desc,
                            severity=ConflictSeverity.HIGH,
                            status=ConflictStatus.DETECTED,
                            agents_involved=[email],
                            conflicting_positions={b1["title"]: "Conflict", b2["title"]: "Conflict"},
                            detected_at=datetime.datetime.utcnow()
                        )
                        db.add(new_conflict)
                        active_descriptions.add(conflict_desc)
    
    # ===== 4. TIME-SLOT CROWDING =====
    # Group by hour to detect VIP bandwidth issues
    hourly_slots = defaultdict(list)
    for m in meetings:
        hour_key = m.scheduled_at.strftime('%Y-%m-%d %H:00')
        hourly_slots[hour_key].append(m)
    
    for hour, hour_meetings in hourly_slots.items():
        if len(hour_meetings) >= 3:
            conflict_desc = f"⚠️ VIP bandwidth warning: {len(hour_meetings)} meetings scheduled in hour {hour}"
            detected_conflicts.append({
                "type": "crowding",
                "severity": "medium",
                "description": conflict_desc,
                "affected_meetings": [str(m.id) for m in hour_meetings],
                "hour": hour
            })
    
    # ===== 5. OVERDUE ACTION ITEMS =====
    overdue_cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    overdue_res = await db.execute(
        select(ActionItem)
        .where(ActionItem.status == ActionItemStatus.PENDING)
        .where(ActionItem.due_date < overdue_cutoff)
    )
    overdue_items = overdue_res.scalars().all()
    
    for item in overdue_items:
        days_overdue = (datetime.datetime.utcnow().date() - item.due_date).days
        detected_conflicts.append({
            "type": "overdue_action",
            "severity": "medium",
            "description": f"📋 Action item overdue by {days_overdue} days: '{item.description[:50]}...'",
            "affected_item": str(item.id)
        })
    
    await db.commit()
    
    # Broadcast to connected clients
    await ws_manager.broadcast({
        "type": "reconciliation_complete",
        "conflicts_found": len(detected_conflicts),
        "auto_resolved": len(auto_resolved),
        "timestamp": datetime.datetime.utcnow().isoformat()
    })
    
    return {
        "status": "reconciliation_complete",
        "scan_time": datetime.datetime.utcnow().isoformat(),
        "conflicts_detected": len(detected_conflicts),
        "auto_resolved": len(auto_resolved),
        "breakdown": {
            "same_slot": len([c for c in detected_conflicts if c["type"] == "same_slot"]),
            "venue": len([c for c in detected_conflicts if c["type"] == "venue"]),
            "vip_double_booking": len([c for c in detected_conflicts if c["type"] == "vip_double_booking"]),
            "crowding": len([c for c in detected_conflicts if c["type"] == "crowding"]),
            "overdue_action": len([c for c in detected_conflicts if c["type"] == "overdue_action"])
        },
        "details": detected_conflicts[:20]  # Return top 20 conflicts
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    import asyncio
    
    # Authenticate
    user_id = "anonymous"
    if token:
        payload = verify_token(token, "access")
        if payload:
            user_id = payload.get("sub")
    
    await ws_manager.connect(websocket, user_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({"type": "connected", "user_id": user_id})
        
        while True:
            try:
                # Wait for message with timeout (heartbeat every 30 seconds)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
                else:
                    # Echo or handle other messages
                    await websocket.send_json({"type": "ack", "message": data})
                    
            except asyncio.TimeoutError:
                # Send heartbeat ping to keep connection alive
                try:
                    await websocket.send_json({"type": "heartbeat", "status": "alive"})
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        # Log but don't crash
        print(f"WebSocket error for {user_id}: {e}")
    finally:
        ws_manager.disconnect(websocket, user_id)
