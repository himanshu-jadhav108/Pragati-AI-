from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.models.entities import Match, Activity, FieldEvent, ProgressUpdate, AuditLog, Project

class ApprovalService:
    @staticmethod
    def approve_match(db: Session, match_id: str, decided_by: str = "Chief Planner", notes: Optional[str] = None) -> Dict[str, Any]:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match candidate not found")

        # Idempotency check
        if match.decision == "APPROVED":
            return {
                "message": "Match has already been approved",
                "match_id": match.id,
                "status": "ALREADY_APPROVED"
            }

        event: FieldEvent = match.event
        activity: Activity = match.candidate_activity
        if not activity:
            raise HTTPException(status_code=400, detail="Match has no associated activity")

        # Capture before state
        before_state = {
            "activity_id": activity.activity_id,
            "actual_progress": activity.actual_progress,
            "actual_quantity": activity.actual_quantity,
            "actual_start": activity.actual_start,
            "actual_finish": activity.actual_finish,
            "status": activity.status
        }

        # Determine new progress & quantity values safely
        new_progress = activity.actual_progress
        if event.progress_percent is not None:
            new_progress = max(activity.actual_progress, min(100.0, event.progress_percent))
        elif event.status == "COMPLETED":
            new_progress = 100.0

        new_quantity = activity.actual_quantity
        if event.quantity is not None and event.quantity > 0:
            new_quantity = max(activity.actual_quantity, event.quantity)

        # Status and date updates
        new_status = activity.status
        if new_progress >= 100.0 or event.status == "COMPLETED":
            new_status = "COMPLETED"
            if not activity.actual_finish:
                activity.actual_finish = event.event_date or datetime.utcnow().strftime("%Y-%m-%d")
        elif new_progress > 0:
            new_status = "IN_PROGRESS"
            if not activity.actual_start:
                activity.actual_start = event.event_date or datetime.utcnow().strftime("%Y-%m-%d")

        # Apply schedule updates to Activity
        activity.actual_progress = new_progress
        activity.actual_quantity = new_quantity
        activity.status = new_status
        if not activity.actual_start and event.event_date:
            activity.actual_start = event.event_date

        # Update Match record
        match.decision = "APPROVED"
        match.decided_by = decided_by
        match.decided_at = datetime.utcnow()
        match.decision_notes = notes

        # Recalculate Project Overall Progress
        project: Project = activity.project
        if project:
            all_acts = db.query(Activity).filter(Activity.project_id == project.id).all()
            if all_acts:
                project.actual_progress = round(sum(a.actual_progress for a in all_acts) / len(all_acts), 2)

        # Capture after state
        after_state = {
            "activity_id": activity.activity_id,
            "actual_progress": activity.actual_progress,
            "actual_quantity": activity.actual_quantity,
            "actual_start": activity.actual_start,
            "actual_finish": activity.actual_finish,
            "status": activity.status
        }

        # Create ProgressUpdate log
        prog_update = ProgressUpdate(
            activity_id=activity.activity_id,
            event_id=event.id,
            match_id=match.id,
            before_progress=before_state["actual_progress"],
            after_progress=after_state["actual_progress"],
            before_quantity=before_state["actual_quantity"],
            after_quantity=after_state["actual_quantity"],
            before_status=before_state["status"],
            after_status=after_state["status"],
            applied_by=decided_by,
            applied_at=datetime.utcnow()
        )
        db.add(prog_update)

        # Create AuditLog record
        audit = AuditLog(
            event_id=event.id,
            document_id=event.document_id,
            match_id=match.id,
            ai_top_activity_id=match.activity_id,
            ai_score=match.final_score,
            ai_confidence=match.confidence_tier,
            action="APPROVE",
            final_activity_id=activity.activity_id,
            previous_state=before_state,
            resulting_state=after_state,
            actor=decided_by,
            timestamp=datetime.utcnow(),
            notes=notes or "Approved AI recommended match"
        )
        db.add(audit)

        db.commit()

        return {
            "message": "Update approved and committed to schedule",
            "match_id": match.id,
            "activity_id": activity.activity_id,
            "before_state": before_state,
            "after_state": after_state
        }

    @staticmethod
    def edit_and_approve(
        db: Session,
        match_id: str,
        override_activity_id: str,
        new_progress_percent: Optional[float] = None,
        new_actual_quantity: Optional[float] = None,
        new_status: Optional[str] = None,
        decided_by: str = "Chief Planner",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match candidate not found")

        target_activity = db.query(Activity).filter(Activity.activity_id == override_activity_id).first()
        if not target_activity:
            raise HTTPException(status_code=404, detail=f"Target activity '{override_activity_id}' not found")

        event: FieldEvent = match.event

        before_state = {
            "activity_id": target_activity.activity_id,
            "actual_progress": target_activity.actual_progress,
            "actual_quantity": target_activity.actual_quantity,
            "status": target_activity.status
        }

        # Apply overridden values
        if new_progress_percent is not None:
            target_activity.actual_progress = min(100.0, max(0.0, new_progress_percent))
        elif event.progress_percent is not None:
            target_activity.actual_progress = min(100.0, max(0.0, event.progress_percent))
        elif event.status == "COMPLETED":
            target_activity.actual_progress = 100.0

        if new_actual_quantity is not None:
            target_activity.actual_quantity = new_actual_quantity
        elif event.quantity is not None:
            target_activity.actual_quantity = event.quantity

        if new_status:
            target_activity.status = new_status
        elif target_activity.actual_progress >= 100.0:
            target_activity.status = "COMPLETED"
            target_activity.actual_finish = event.event_date or datetime.utcnow().strftime("%Y-%m-%d")

        if not target_activity.actual_start and event.event_date:
            target_activity.actual_start = event.event_date

        match.decision = "EDITED"
        match.decided_by = decided_by
        match.decided_at = datetime.utcnow()
        match.decision_notes = notes

        # Recalculate Project Overall Progress
        project: Project = target_activity.project
        if project:
            all_acts = db.query(Activity).filter(Activity.project_id == project.id).all()
            if all_acts:
                project.actual_progress = round(sum(a.actual_progress for a in all_acts) / len(all_acts), 2)

        after_state = {
            "activity_id": target_activity.activity_id,
            "actual_progress": target_activity.actual_progress,
            "actual_quantity": target_activity.actual_quantity,
            "status": target_activity.status
        }

        # Audit with AI suggestion vs Human decision
        audit = AuditLog(
            event_id=event.id,
            document_id=event.document_id,
            match_id=match.id,
            ai_top_activity_id=match.activity_id,
            ai_score=match.final_score,
            ai_confidence=match.confidence_tier,
            action="EDIT_APPROVE",
            final_activity_id=target_activity.activity_id,
            previous_state=before_state,
            resulting_state=after_state,
            actor=decided_by,
            timestamp=datetime.utcnow(),
            notes=notes or f"Planner edited activity from {match.activity_id} to {target_activity.activity_id}"
        )
        db.add(audit)
        db.commit()

        return {
            "message": "Planner override approved and committed to schedule",
            "match_id": match.id,
            "ai_suggested_id": match.activity_id,
            "final_activity_id": target_activity.activity_id,
            "before_state": before_state,
            "after_state": after_state
        }

    @staticmethod
    def reject_match(db: Session, match_id: str, decided_by: str = "Chief Planner", reason: str = "Rejected by planner") -> Dict[str, Any]:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        match.decision = "REJECTED"
        match.decided_by = decided_by
        match.decided_at = datetime.utcnow()
        match.decision_notes = reason

        # Log rejection audit trail (no schedule mutation)
        audit = AuditLog(
            event_id=match.event_id,
            document_id=match.event.document_id if match.event else None,
            match_id=match.id,
            ai_top_activity_id=match.activity_id,
            ai_score=match.final_score,
            ai_confidence=match.confidence_tier,
            action="REJECT",
            final_activity_id=None,
            previous_state=None,
            resulting_state=None,
            actor=decided_by,
            timestamp=datetime.utcnow(),
            notes=f"Rejected AI match suggestion: {reason}"
        )
        db.add(audit)
        db.commit()

        return {
            "message": "Match rejected. Schedule remains untouched.",
            "match_id": match.id,
            "status": "REJECTED"
        }
