from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.entities import Activity

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

class HistoryService:
    def __init__(self, db: Session, project_id: str = "OIL-DNPE-2026"):
        self.db = db
        self.project_id = project_id

    def get_historical_insights(self, discipline: Optional[str] = None) -> Dict[str, Any]:
        """
        Computes historical execution patterns from already-approved activity data:
        1. Planned duration vs actual duration in days per activity
        2. Variance (actual - planned) in days
        3. Discipline aggregations: avg variance, count of overruns vs on-time/early
        4. Project-level summary sorted by discipline with the most overrun days first
        """
        query = self.db.query(Activity).filter(
            Activity.actual_start.isnot(None),
            Activity.actual_finish.isnot(None)
        )
        if self.project_id:
            query = query.filter(Activity.project_id == self.project_id)
        if discipline:
            query = query.filter(Activity.discipline == discipline)

        activities = query.all()

        records = []
        discipline_stats: Dict[str, Dict[str, Any]] = {}

        total_activities = 0
        total_overrun_activities = 0
        total_ontime_activities = 0
        total_variance_days = 0

        for act in activities:
            p_start = parse_date(act.planned_start)
            p_finish = parse_date(act.planned_finish)
            a_start = parse_date(act.actual_start)
            a_finish = parse_date(act.actual_finish)

            if p_start and p_finish:
                planned_duration = max(1, (p_finish - p_start).days + 1)
            else:
                planned_duration = 1

            if a_start and a_finish:
                actual_duration = max(1, (a_finish - a_start).days + 1)
            else:
                actual_duration = planned_duration

            variance = actual_duration - planned_duration
            is_overrun = variance > 0

            total_activities += 1
            if is_overrun:
                total_overrun_activities += 1
            else:
                total_ontime_activities += 1
            total_variance_days += variance

            rec = {
                "activity_id": act.activity_id,
                "description": act.description,
                "discipline": act.discipline,
                "location": act.location,
                "equipment_id": act.equipment_id,
                "planned_start": act.planned_start,
                "planned_finish": act.planned_finish,
                "actual_start": act.actual_start,
                "actual_finish": act.actual_finish,
                "planned_duration_days": planned_duration,
                "actual_duration_days": actual_duration,
                "variance_days": variance,
                "is_overrun": is_overrun,
                "status": "OVERRUN" if is_overrun else ("ON_TIME" if variance == 0 else "AHEAD")
            }
            records.append(rec)

            disc = act.discipline or "General"
            if disc not in discipline_stats:
                discipline_stats[disc] = {
                    "discipline": disc,
                    "total_count": 0,
                    "overrun_count": 0,
                    "ontime_early_count": 0,
                    "total_variance_days": 0,
                    "overrun_days": 0,
                    "average_variance_days": 0.0
                }

            st = discipline_stats[disc]
            st["total_count"] += 1
            st["total_variance_days"] += variance
            if is_overrun:
                st["overrun_count"] += 1
                st["overrun_days"] += variance
            else:
                st["ontime_early_count"] += 1

        discipline_summary = []
        for disc, st in discipline_stats.items():
            if st["total_count"] > 0:
                st["average_variance_days"] = round(st["total_variance_days"] / st["total_count"], 2)
            discipline_summary.append(st)

        # Sort by total overrun days descending (most overrun days first)
        discipline_summary.sort(key=lambda d: (d["overrun_days"], d["average_variance_days"]), reverse=True)

        # Sort individual records: overruns with highest variance first
        records.sort(key=lambda r: (r["variance_days"], r["activity_id"]), reverse=True)

        avg_project_variance = round(total_variance_days / total_activities, 2) if total_activities > 0 else 0.0

        return {
            "project_id": self.project_id,
            "total_completed_activities": total_activities,
            "total_overrun_count": total_overrun_activities,
            "total_ontime_early_count": total_ontime_activities,
            "average_variance_days": avg_project_variance,
            "discipline_summary": discipline_summary,
            "activities": records
        }
