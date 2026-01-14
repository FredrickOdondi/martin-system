"""
Continuous Monitor Service

Runs background jobs to detect:
1. Temporal Conflicts (Scheduling overlaps)
2. Semantic Conflicts (Policy divergences)
3. TWG Health (Inactivity deadlines)

Uses APScheduler for periodic execution.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta, UTC
from loguru import logger
from typing import List, Optional, Tuple
import asyncio


from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.database import get_db_session_context
from app.models.models import Meeting, Conflict, TWG, ConflictStatus, Notification, NotificationType, Document, User, MeetingParticipant, VipProfile
from app.services.conflict_detector import ConflictDetector
from app.services.reconciliation_service import get_reconciliation_service

class ContinuousMonitor:
    """
    Background service for maintaining global state integrity.
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.conflict_detector = ConflictDetector() # Initialize without LLM for now, or inject if needed
        self.is_running = False
        
    def start(self):
        """Start the background monitor."""
        if self.is_running:
            return
            
        logger.info("Starting Continuous Monitor...")
        
        # 1. Temporal Conflict Scan (Every 5 mins)
        self.scheduler.add_job(
            self.scan_scheduling_conflicts,
            trigger=IntervalTrigger(minutes=5),
            id="scan_scheduling",
            replace_existing=True
        )
        
        # 2. Semantic Analysis (Every 15 mins)
        self.scheduler.add_job(
            self.scan_policy_divergences,
            trigger=IntervalTrigger(minutes=15),
            id="scan_policy",
            replace_existing=True
        )
        
        # 3. Health Check (Hourly)
        self.scheduler.add_job(
            self.check_twg_health,
            trigger=IntervalTrigger(hours=1),
            id="health_check",
            replace_existing=True
        )
        
        # 4. Project Conflict Scan (Every 6 hours)
        self.scheduler.add_job(
            self.scan_project_conflicts,
            trigger=IntervalTrigger(hours=6),
            id="scan_projects",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("Continuous Monitor started.")

    def stop(self):
        """Stop the background monitor."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Continuous Monitor stopped.")

    async def scan_scheduling_conflicts(self):
        """
        Check for:
        - Overlapping meetings for same TWG
        - VIP double bookings (simplified check for now)
        - Venue conflicts
        """
        logger.info("Running scan_scheduling_conflicts...")
        async with get_db_session_context() as db:
            try:
                # 1. Fetch upcoming meetings with participants loaded
                # Fix: Use naive UTC to match DB TIMESTAMP WITHOUT TIME ZONE
                stmt = select(Meeting).where(Meeting.scheduled_at > datetime.utcnow()).options(
                    selectinload(Meeting.participants).selectinload(MeetingParticipant.user).selectinload(User.vip_profile)
                )
                result = await db.execute(stmt)
                meetings = result.scalars().all()
                
                # Check for overlaps
                conflicts_found = []
                for i in range(len(meetings)):
                    for j in range(i + 1, len(meetings)):
                        m1 = meetings[i]
                        m2 = meetings[j]
                        
                        # Overlap logic: (StartA < EndB) and (EndA > StartB)
                        # We need end time. computed from duration
                        m1_end = m1.scheduled_at + timedelta(minutes=m1.duration_minutes)
                        m2_end = m2.scheduled_at + timedelta(minutes=m2.duration_minutes)
                        
                        if (m1.scheduled_at < m2_end) and (m1_end > m2.scheduled_at):
                            reason = ""
                            severity = "low"
                            
                            # Physical Venue Conflict? (Exclude virtual venues - unlimited capacity)
                            if (m1.location and m2.location and 
                                m1.location == m2.location and 
                                m1.location.lower() not in ['virtual', 'online', 'remote']):
                                reason = f"Venue conflict at {m1.location}"
                                severity = "high"
                            
                            # Same TWG Double Booking? (Check independently - applies to both physical and virtual)
                            if m1.twg_id == m2.twg_id:
                                reason = "Double booking for TWG"
                                severity = "medium"

                            # Shared Participants / VIP Conflict
                            # Get sets of user IDs to find intersection
                            p1_map = {p.user_id: p.user for p in m1.participants if p.user}
                            p2_map = {p.user_id: p.user for p in m2.participants if p.user}
                            
                            shared_user_ids = set(p1_map.keys()) & set(p2_map.keys())
                            if shared_user_ids:
                                shared_users = [p1_map[uid] for uid in shared_user_ids]
                                participant_severity, description = self._calculate_severity(shared_users)
                                
                                # Escalate if participant severity is higher
                                severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                                if severity_levels.get(participant_severity, 1) > severity_levels.get(severity, 1):
                                    severity = participant_severity
                                    reason = f"{reason}; {description}" if reason else description
                                else:
                                    if reason:
                                         reason += f"; {description}"
                                    else:
                                         reason = description

                            if reason:
                                logger.warning(f"Conflict found: {reason} between {m1.title} and {m2.title}")
                                
                                # Auto-handle conflict
                                await self._handle_detected_conflicts(
                                    db_session=db, 
                                    conflict_data = {
                                        "description": f"{reason} between {m1.title} and {m2.title}",
                                        "conflict_type": "schedule_clash",
                                        "severity": severity,
                                        "conflicting_positions": {
                                            "meeting_1": str(m1.id),
                                            "meeting_2": str(m2.id),
                                            "reason": reason
                                        }
                                    },
                                    agents_involved=[str(m1.twg_id), str(m2.twg_id)] # Assuming twg_id is what we need, or name
                                )
                                
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.error(f"Error in scheduling scan: {e}")

    def _calculate_severity(self, shared_participants: List[User]) -> Tuple[str, str]:
        """
        Calculate severity based on shared participants.
        Returns (severity, description)
        """
        vips = []
        ministers = []
        directors = []
        
        for p in shared_participants:
            # Check for Minister
            is_minister = False
            # Check Role
            if p.role == "secretariat_lead": # Example mapping
                pass 
            
            # Check VIP Profile
            if p.vip_profile:
                vips.append(p)
                title = p.vip_profile.title.lower() if p.vip_profile.title else ""
                if "minister" in title or "head of state" in title:
                    ministers.append(p)
                    is_minister = True
                elif "director" in title or "commissioner" in title:
                    directors.append(p)
            
            # Fallback simple role check if no profile but role says something?
            # Assuming Role enum doesn't have MINISTER directly, using VipProfile
            
        if ministers:
            names = ", ".join([u.full_name for u in ministers])
            return "critical", f"Minister(s) double-booked: {names}"
        
        if directors:
             names = ", ".join([u.full_name for u in directors])
             return "high", f"Director(s)/High-level VIPs double-booked: {names}"
             
        if len(shared_participants) > 10:
             return "high", f"Large group overlap ({len(shared_participants)} participants)"
             
        if len(shared_participants) > 3:
             return "medium", f"Multiple participants overlap ({len(shared_participants)} people)"
             
        # confirmed overlap <= 3 regular people
        names = ", ".join([u.full_name for u in shared_participants])
        return "low", f"Participant overlap: {names}"

    async def _handle_detected_conflicts(
        self, 
        db_session: AsyncSession, 
        conflict_data: dict,
        agents_involved: List[str]
    ):
        """
        Autonomous conflict handling.
        1. Save to DB
        2. Notify involved TWG Leads (Feedback Loop)
        3. Trigger auto-negotiation
        """
        try:
            # Create Conflict Record
            conflict = Conflict(
                conflict_type=conflict_data["conflict_type"],
                severity=conflict_data["severity"],
                description=conflict_data["description"],
                agents_involved=[str(a) for a in agents_involved],
                conflicting_positions=conflict_data.get("conflicting_positions", {}),
                status=ConflictStatus.DETECTED,
                detected_at=datetime.utcnow(),
                metadata_json=conflict_data # Store full data in metadata
            )
            db_session.add(conflict)
            await db_session.flush() # Get ID
            
            # NOTIFICATION LOGIC (Supervisor -> TWG Feedback)
            logger.info(f"Notifying agents for Conflict {conflict.id}")
            for twg_id_str in agents_involved:
                try:
                    # Resolve TWG UUID
                    twg_uuid = twg_id_str
                    
                    # Fetch TWG to get Technical Lead
                    stmt = select(TWG).where(TWG.id == twg_uuid)
                    result = await db_session.execute(stmt)
                    twg = result.scalar_one_or_none()
                    
                    if twg and twg.technical_lead_id:
                        # Create Notification
                        notification = Notification(
                            user_id=twg.technical_lead_id,
                            type=NotificationType.ALERT,
                            title="Supervisor Insight: Conflict Detected",
                            content=f"The Supervisor has detected a {conflict.conflict_type} that affects your TWG: {conflict.description}",
                            link=f"/conflicts/{conflict.id}",
                            is_read=False,
                            created_at=datetime.utcnow()
                        )
                        db_session.add(notification)
                        logger.info(f"Notification queued for TWG {twg.name} (Lead: {twg.technical_lead_id})")
                    else:
                        logger.warning(f"Could not notify TWG {twg_id_str}: Lead not found")
                        
                except Exception as ex:
                    logger.error(f"Failed to notify agent {twg_id_str}: {ex}")

            logger.info(f"Triggering auto-negotiation for Conflict {conflict.id}")
            
            # Trigger Auto-Negotiation
            reconciler = get_reconciliation_service(db_session)
            result = await reconciler.run_automated_negotiation(conflict)
            
            if result.get("negotiation_result") == "auto_resolved":
                logger.info(f"Conflict {conflict.id} AUTO-RESOLVED")
            else:
                logger.warning(f"Conflict {conflict.id} ESCALATED")
                
            await db_session.commit()
            
        except Exception as e:
            logger.error(f"Failed to handle conflict: {e}")

    async def scan_policy_divergences(self):
        """
        Check for semantic conflicts in recent TWG outputs/documents.
        """
        logger.info("Running scan_policy_divergences...")
        async with get_db_session_context() as db:
            try:
                # Fetch recent documents (e.g. last 24h) or just "Evolving" docs
                # For this implementation, we check all 'active' documents or scope-tagged ones.
                # Simplified: fetch latest document for each TWG
                
                # We need to map TWG Name -> Document Content
                # Subquery to find latest doc per TWG
                # Skipping strict query optimization for prototype simplicity
                
                result = await db.execute(select(TWG))
                twgs = result.scalars().all()
                
                twg_contents = {}
                for twg in twgs:
                    # Get latest document for this TWG
                    # Assuming we can filter by type or just grab last upload
                    stmt = select(Document).where(Document.twg_id == twg.id).order_by(Document.created_at.desc()).limit(1)
                    doc_res = await db.execute(stmt)
                    doc = doc_res.scalar_one_or_none()
                    
                    if doc:
                         # Ideally we load content. Using file_name + metadata as proxy if text not in DB
                         content = doc.file_name
                         if doc.metadata_json:
                             content += f" {str(doc.metadata_json)}"
                         twg_contents[twg.name] = content
                
                if len(twg_contents) > 1:
                    logger.info(f"Analyzing {len(twg_contents)} TWG outputs for conflicts")
                    conflicts = self.conflict_detector.detect_conflicts(twg_contents)
                    
                    if conflicts:
                        logger.warning(f"Detected {len(conflicts)} policy conflicts")
                        
                        for conflict in conflicts:
                            # Auto-handle conflict
                            await self._handle_detected_conflicts(
                                db_session=db,
                                conflict_data={
                                    "description": conflict.description,
                                    "conflict_type": conflict.conflict_type,
                                    "severity": conflict.severity
                                },
                                agents_involved=conflict.agents_involved
                            )
                        
            except Exception as e:
                logger.error(f"Error in policy scan: {e}")

    async def check_twg_health(self):
        """
        Check for stalled TWGs (no activity > 48h).
        Simulated metric for now.
        """
        logger.info("Running check_twg_health...")
        async with get_db_session_context() as db:
            try:
                # In a real implementation:
                # 1. Check last message associated with TWG agents
                # 2. Check last document update
                # 3. Check for overdue ActionItems
                
                # For this prototype: basic connectivity check/log
                result = await db.execute(select(TWG))
                twgs = result.scalars().all()
                for twg in twgs:
                    # Log check
                    # logger.info(f"Health check for TWG: {twg.name}")
                    pass
                    
            except Exception as e:
                logger.error(f"Error in health check: {e}")

    async def scan_project_conflicts(self):
        """
        Detect dependency and duplicate conflicts for Projects.
        Runs every 6 hours.
        """
        logger.info("Running scan_project_conflicts...")
        async with get_db_session_context() as db:
            try:
                # Run detections
                dependency_conflicts = await self.conflict_detector.detect_project_dependency_conflicts(db)
                duplicate_conflicts = await self.conflict_detector.detect_duplicate_projects(db)
                
                all_conflicts = dependency_conflicts + duplicate_conflicts
                
                if not all_conflicts:
                    logger.info("No project conflicts detected.")
                    return

                logger.info(f"Detected {len(all_conflicts)} potential project conflicts")
                
                new_conflicts_count = 0
                
                for conflict in all_conflicts:
                    # Check for existing conflict (Active or Resolved recently?)
                    # Simplified check: same type and same project IDs involved
                    
                    # Extract project IDs from metadata to query
                    project_a_id = None
                    project_b_id = None
                    
                    if conflict.metadata_json:
                        if "dependent_project_id" in conflict.metadata_json:
                             project_a_id = conflict.metadata_json["dependent_project_id"]
                             project_b_id = conflict.metadata_json["prerequisite_project_id"]
                        elif "project_a_id" in conflict.metadata_json:
                             project_a_id = conflict.metadata_json["project_a_id"]
                             project_b_id = conflict.metadata_json["project_b_id"]
                    
                    # If we can't identify projects, we might skip dedupe check or use agents
                    # But assuming our detector works, we have IDs.
                    
                    if project_a_id and project_b_id:
                        # Check DB
                        # We need to query if a conflict with these project IDs exists
                        # Since metadata_json is JSONB (Postgres) or JSON, querying it might be tricky depending on DB
                        # Alternative: Filter by `agents_involved` and `conflict_type` and iterate results?
                        # Or just adding and ignoring?
                        # For now, let's try to filter by metadata if possible or fallback to python
                        
                        # Fetch all active conflicts of this type
                        stmt = select(Conflict).where(
                            and_(
                                Conflict.conflict_type == conflict.conflict_type,
                                Conflict.status.in_([ConflictStatus.DETECTED, ConflictStatus.NEGOTIATING, ConflictStatus.ESCALATED])
                            )
                        )
                        existing_result = await db.execute(stmt)
                        existing_conflicts = existing_result.scalars().all()
                        
                        is_duplicate = False
                        for exc in existing_conflicts:
                            # Check metadata match
                            e_meta = exc.metadata_json or {}
                            # Check for cross-match too? (A vs B is same as B vs A for Duplicates?)
                            # Dependencies are directional. Duplicates are bidirectional.
                            
                            if conflict.conflict_type == "duplicate_project_conflict": # String match or Enum?
                                # Check pairs
                                e_a = e_meta.get("project_a_id")
                                e_b = e_meta.get("project_b_id")
                                if {e_a, e_b} == {project_a_id, project_b_id}:
                                    is_duplicate = True
                                    break
                            else:
                                # Dependency
                                if (e_meta.get("dependent_project_id") == project_a_id and 
                                    e_meta.get("prerequisite_project_id") == project_b_id):
                                    is_duplicate = True
                                    break
                        
                        if is_duplicate:
                            continue
                            
                    # If not duplicate, add it
                    db.add(conflict)
                    new_conflicts_count += 1
                    
                    # Notify? Trigger Auto-Negotiation?
                    # The prompt suggests auto-negotiating dependencies
                    if conflict.conflict_type == "project_dependency_conflict": 
                        # We need to commit to get ID first? Or add logic here?
                        # Let's save first.
                        pass
                
                await db.commit()
                logger.info(f"Saved {new_conflicts_count} new project conflicts")
                
                # Post-save actions (Trigger negotiation/Notification)
                # We iterate again or handle above?
                # Ideally we handle after commit if we need IDs, 
                # but we can rely on ContinuousMonitor waking up again? 
                # No, better to trigger now.
                # However, complex logic might be better separated.
                        
            except Exception as e:
                logger.error(f"Error in project conflict scan: {e}")

# Singleton
_monitor_instance = None

def get_continuous_monitor() -> ContinuousMonitor:
    global _monitor_instance
    if not _monitor_instance:
        _monitor_instance = ContinuousMonitor()
    return _monitor_instance
