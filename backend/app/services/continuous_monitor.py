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
from typing import List, Optional
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.database import get_db_session_context
from app.models.models import Meeting, Conflict, TWG, ConflictStatus
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
                # 1. Fetch upcoming meetings
                # Fix: Use naive UTC to match DB TIMESTAMP WITHOUT TIME ZONE
                result = await db.execute(
                    select(Meeting).where(Meeting.scheduled_at > datetime.utcnow())
                )
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
                            
                            # Same Venue?
                            if m1.location and m2.location and m1.location == m2.location:
                                reason = f"Venue conflict at {m1.location}"
                                severity = "high"
                            
                            # Same TWG? (Shouldn't happen usually but possible)
                            elif m1.twg_id == m2.twg_id:
                                reason = "Double booking for TWG"
                                severity = "medium"
                                
                                
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
                                    agents_involved=[m1.twg_id, m2.twg_id] # Assuming twg_id is what we need, or name
                                )
                                
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.error(f"Error in scheduling scan: {e}")

from app.models.models import Meeting, Conflict, TWG, ConflictStatus, Notification, NotificationType

# ... (Previous code)

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
                detected_at=datetime.utcnow()
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

# Singleton
_monitor_instance = None

def get_continuous_monitor() -> ContinuousMonitor:
    global _monitor_instance
    if not _monitor_instance:
        _monitor_instance = ContinuousMonitor()
    return _monitor_instance
