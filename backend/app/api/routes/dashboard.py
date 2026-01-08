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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get current conflicts/inconsistencies detected by the Supervisor.
    """
    from app.models.models import Conflict, ConflictStatus
    
    result = await db.execute(
        select(Conflict)
        .where(Conflict.status != ConflictStatus.RESOLVED)
        .where(Conflict.status != ConflictStatus.DISMISSED)
        .order_by(desc(Conflict.detected_at))
    )
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
    await ws_manager.broadcast_json({"type": "conflict_resolved", "id": str(conflict.id)})
    
    return conflict

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    # Authenticate
    user_id = "anonymous"
    if token:
        payload = verify_token(token, "access")
        if payload:
            user_id = payload.get("sub")
    
    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep alive and handle potential incoming messages
            data = await websocket.receive_text()
            # Handle incoming messages if needed, e.g., ping/pong
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
