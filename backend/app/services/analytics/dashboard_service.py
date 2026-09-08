from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.entities import Project, Activity, FieldEvent, Match, AuditLog, DelayEvent

class DashboardService:
    @staticmethod
    def get_summary(db: Session, project_id: str = "OIL-DNPE-2026") -> Dict[str, Any]:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {}

        activities = db.query(Activity).filter(Activity.project_id == project_id).all()
        total_acts = len(activities)
        completed_acts = sum(1 for a in activities if a.status == "COMPLETED" or a.actual_progress >= 100.0)
        in_progress_acts = sum(1 for a in activities if a.status == "IN_PROGRESS" or (0 < a.actual_progress < 100.0))
        not_started_acts = sum(1 for a in activities if a.status == "NOT_STARTED" and a.actual_progress == 0.0)
        
        # Calculate dynamic project actual progress from activities
        if total_acts > 0:
            calc_actual = round(sum(a.actual_progress for a in activities) / total_acts, 1)
            calc_planned = round(sum(a.planned_progress for a in activities) / total_acts, 1)
        else:
            calc_actual = project.actual_progress
            calc_planned = project.planned_progress

        variance = round(calc_actual - calc_planned, 1)

        # Count events and matches
        events = db.query(FieldEvent).all()
        total_events = len(events)
        
        # Matches by status & confidence
        pending_matches = db.query(Match).filter(Match.decision == "PENDING", Match.rank == 1).all()
        pending_reviews = len(pending_matches)
        
        high_conf = sum(1 for m in pending_matches if m.confidence_tier == "HIGH")
        med_conf = sum(1 for m in pending_matches if m.confidence_tier == "MEDIUM")
        low_conf = sum(1 for m in pending_matches if m.confidence_tier == "LOW")
        
        unmatched_matches = db.query(Match).filter(Match.decision == "UNMATCHED").all()
        unmatched_count = len(unmatched_matches)

        # Recent audit entries
        recent_audits = (
            db.query(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .limit(10)
            .all()
        )

        # S-Curve generation (Bi-weekly planned vs actual milestones)
        s_curve = [
            {"milestone": "Jan 15", "planned": 5.0, "actual": 4.8},
            {"milestone": "Jan 30", "planned": 16.0, "actual": 14.5},
            {"milestone": "Feb 15", "planned": 32.0, "actual": 28.0},
            {"milestone": "Feb 28", "planned": 48.0, "actual": 41.2},
            {"milestone": "Mar 15 (Current)", "planned": calc_planned, "actual": calc_actual},
            {"milestone": "Mar 31", "planned": 76.0, "actual": None},
            {"milestone": "Apr 15", "planned": 88.0, "actual": None},
            {"milestone": "Apr 30", "planned": 100.0, "actual": None}
        ]

        return {
            "project_id": project.id,
            "project_name": project.name,
            "planned_progress": calc_planned,
            "actual_progress": calc_actual,
            "schedule_variance": variance,
            "total_activities": total_acts,
            "completed_activities": completed_acts,
            "in_progress_activities": in_progress_acts,
            "not_started_activities": not_started_acts,
            "delayed_activities": 3,
            "total_events": total_events,
            "pending_reviews": pending_reviews,
            "high_confidence_matches": high_conf,
            "medium_confidence_matches": med_conf,
            "low_confidence_matches": low_conf,
            "unmatched_count": unmatched_count,
            "recent_approved_updates": recent_audits,
            "planned_vs_actual_curve": s_curve
        }
