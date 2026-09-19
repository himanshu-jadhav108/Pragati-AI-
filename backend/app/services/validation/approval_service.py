from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.models.entities import Match, Activity, FieldEvent, ProgressUpdate, AuditLog, Project
from backend.app.core.config import settings

class ApprovalService:
    @staticmethod
    def approve_match(db: Session, match_id: str, decided_by: str = "Chief Planner", notes: Optional[str] = None) -> Dict[str, Any]:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match candidate not found")

        # Idempotency safeguard
        if match.decision in ["APPROVED", "EDITED_APPROVED"]:
            return {
                "message": "Match has already been approved",
                "match_id": match.id,
                "status": "ALREADY_APPROVED"
            }
        if match.decision == "REJECTED":
            raise HTTPException(status_code=400, detail="Cannot approve a previously rejected match candidate")

        event: Optional[FieldEvent] = match.event
        if not event:
            raise HTTPException(status_code=400, detail="Associated field event not found")

        activity: Optional[Activity] = match.candidate_activity
        if not activity:
            raise HTTPException(status_code=400, detail="Match has no associated schedule activity")

        # Capture before state
        before_state = {
            "activity_id": activity.activity_id,
            "actual_progress": activity.actual_progress,
            "actual_quantity": activity.actual_quantity,
            "actual_start": activity.actual_start,
            "actual_finish": activity.actual_finish,
            "status": activity.status
        }

        effective_date = event.event_date or settings.get_effective_date()

        # Temporal validation & sanity checks
        temporal_warning = None
        if activity.status == "COMPLETED" and activity.actual_progress >= 100.0:
            temporal_warning = f"Activity {activity.activity_id} was already recorded as 100% COMPLETED."
        elif activity.actual_start and effective_date < activity.actual_start:
            temporal_warning = f"Temporal conflict: Reported finish date ({effective_date}) is earlier than recorded start ({activity.actual_start})."

        # Determine new progress & quantity values safely (bounded 0-100)
        new_progress = activity.actual_progress
        if event.progress_percent is not None:
            new_progress = max(activity.actual_progress, min(100.0, max(0.0, float(event.progress_percent))))
        elif event.status == "COMPLETED":
            new_progress = 100.0

        new_quantity = activity.actual_quantity
        if event.quantity is not None and event.quantity > 0:
            new_quantity = max(activity.actual_quantity, float(event.quantity))

        # Status and date updates
        new_status = activity.status
        if new_progress >= 100.0 or event.status == "COMPLETED":
            new_status = "COMPLETED"
            activity.actual_finish = effective_date
            if not activity.actual_start:
                activity.actual_start = effective_date
        elif new_progress > 0:
            new_status = "IN_PROGRESS"
            if not activity.actual_start:
                activity.actual_start = effective_date

        # Apply schedule updates to Activity
        activity.actual_progress = new_progress
        activity.actual_quantity = new_quantity
        activity.status = new_status

        # Update Match record
        match.decision = "APPROVED"
        match.decided_by = decided_by
        match.decided_at = datetime.now()
        match.decision_notes = notes

        # Recalculate Project Overall Progress
        project: Optional[Project] = activity.project
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
            applied_at=datetime.now()
        )
        db.add(prog_update)

        # Audit notes with temporal alerts if present
        full_audit_notes = notes or "Approved AI recommended match"
        if temporal_warning:
            full_audit_notes = f"{full_audit_notes} [Warning: {temporal_warning}]"

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
            timestamp=datetime.now(),
            notes=full_audit_notes
        )
        db.add(audit)

        db.commit()

        return {
            "message": "Update approved and committed to schedule",
            "match_id": match.id,
            "activity_id": activity.activity_id,
            "before_state": before_state,
            "after_state": after_state,
            "temporal_warning": temporal_warning
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

        if match.decision in ["APPROVED", "EDITED_APPROVED"]:
            return {
                "message": "Match has already been approved",
                "match_id": match.id,
                "status": "ALREADY_APPROVED"
            }

        target_activity = db.query(Activity).filter(Activity.activity_id == override_activity_id).first()
        if not target_activity:
            raise HTTPException(status_code=404, detail=f"Target activity '{override_activity_id}' not found in master schedule")

        event: FieldEvent = match.event
        if not event:
            raise HTTPException(status_code=400, detail="Associated field event not found")

        effective_date = event.event_date or settings.get_effective_date()

        before_state = {
            "activity_id": target_activity.activity_id,
            "actual_progress": target_activity.actual_progress,
            "actual_quantity": target_activity.actual_quantity,
            "actual_start": target_activity.actual_start,
            "actual_finish": target_activity.actual_finish,
            "status": target_activity.status
        }

        # Apply overridden values safely
        if new_progress_percent is not None:
            target_activity.actual_progress = min(100.0, max(0.0, float(new_progress_percent)))
        elif event.progress_percent is not None:
            target_activity.actual_progress = min(100.0, max(0.0, float(event.progress_percent)))
        elif event.status == "COMPLETED":
            target_activity.actual_progress = 100.0

        if new_actual_quantity is not None:
            target_activity.actual_quantity = max(target_activity.actual_quantity, float(new_actual_quantity))
        elif event.quantity is not None and event.quantity > 0:
            target_activity.actual_quantity = max(target_activity.actual_quantity, float(event.quantity))

        if new_status:
            target_activity.status = new_status
        elif target_activity.actual_progress >= 100.0:
            target_activity.status = "COMPLETED"
            target_activity.actual_finish = effective_date
            if not target_activity.actual_start:
                target_activity.actual_start = effective_date
        elif target_activity.actual_progress > 0:
            target_activity.status = "IN_PROGRESS"
            if not target_activity.actual_start:
                target_activity.actual_start = effective_date

        match.decision = "EDITED_APPROVED"
        match.decided_by = decided_by
        match.decided_at = datetime.now()
        match.decision_notes = notes

        # Recalculate Project Overall Progress
        project: Optional[Project] = target_activity.project
        if project:
            all_acts = db.query(Activity).filter(Activity.project_id == project.id).all()
            if all_acts:
                project.actual_progress = round(sum(a.actual_progress for a in all_acts) / len(all_acts), 2)

        after_state = {
            "activity_id": target_activity.activity_id,
            "actual_progress": target_activity.actual_progress,
            "actual_quantity": target_activity.actual_quantity,
            "actual_start": target_activity.actual_start,
            "actual_finish": target_activity.actual_finish,
            "status": target_activity.status
        }

        # ProgressUpdate record
        prog_update = ProgressUpdate(
            activity_id=target_activity.activity_id,
            event_id=event.id,
            match_id=match.id,
            before_progress=before_state["actual_progress"],
            after_progress=after_state["actual_progress"],
            before_quantity=before_state["actual_quantity"],
            after_quantity=after_state["actual_quantity"],
            before_status=before_state["status"],
            after_status=after_state["status"],
            applied_by=decided_by,
            applied_at=datetime.now()
        )
        db.add(prog_update)

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
            timestamp=datetime.now(),
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

        if match.decision == "REJECTED":
            return {
                "message": "Match has already been rejected",
                "match_id": match.id,
                "status": "ALREADY_REJECTED"
            }

        if match.decision in ["APPROVED", "EDITED_APPROVED"]:
            raise HTTPException(status_code=400, detail="Cannot reject an already committed schedule approval")

        match.decision = "REJECTED"
        match.decided_by = decided_by
        match.decided_at = datetime.now()
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
            timestamp=datetime.now(),
            notes=f"Rejected AI match suggestion: {reason}"
        )
        db.add(audit)
        db.commit()

        return {
            "message": "Match rejected. Schedule remains untouched.",
            "match_id": match.id,
            "status": "REJECTED"
        }

