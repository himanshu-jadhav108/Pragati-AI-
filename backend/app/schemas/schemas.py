from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Project Schemas
class ProjectBase(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    start_date: Optional[str] = None
    finish_date: Optional[str] = None
    planned_progress: float = 0.0
    actual_progress: float = 0.0

class ProjectResponse(ProjectBase):
    class Config:
        from_attributes = True

# Activity Schemas
class ActivityBase(BaseModel):
    activity_id: str
    wbs_id: Optional[str] = None
    description: str
    discipline: str
    location: Optional[str] = None
    equipment_id: Optional[str] = None
    planned_start: Optional[str] = None
    planned_finish: Optional[str] = None
    planned_progress: float = 0.0
    actual_start: Optional[str] = None
    actual_finish: Optional[str] = None
    actual_progress: float = 0.0
    target_quantity: float = 0.0
    actual_quantity: float = 0.0
    unit: Optional[str] = None
    status: str = "NOT_STARTED"

class ActivityResponse(ActivityBase):
    project_id: str
    class Config:
        from_attributes = True

# Document Schemas
class DocumentResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    file_type: str
    file_size: int
    uploaded_by: str
    created_at: datetime
    raw_text: Optional[str] = None
    class Config:
        from_attributes = True

# Field Event Schema
class FieldEventExtract(BaseModel):
    event_date: Optional[str] = None
    discipline: Optional[str] = None
    activity_description: Optional[str] = None
    location: Optional[str] = None
    equipment_id: Optional[str] = None
    status: Optional[str] = None
    progress_percent: Optional[float] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    source_reference: Optional[str] = None
    evidence_text: Optional[str] = None

class FieldEventResponse(FieldEventExtract):
    id: str
    document_id: str
    raw_text: str
    extraction_provider: str
    is_processed: bool
    created_at: datetime
    class Config:
        from_attributes = True

# Match Schemas
class MatchComponentScores(BaseModel):
    score_semantic: float = 0.0
    score_discipline: float = 0.0
    score_entity: float = 0.0
    score_location: float = 0.0
    score_temporal: float = 0.0
    penalty_contradiction: float = 0.0
    final_score: float = 0.0

class MatchResponse(BaseModel):
    id: str
    event_id: str
    activity_id: Optional[str] = None
    activity: Optional[ActivityResponse] = None
    scores: MatchComponentScores
    rank: int = 1
    confidence_tier: str
    rationale: Optional[str] = None
    contradictions: Optional[str] = None
    decision: str
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    decision_notes: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class MatchCandidate(BaseModel):
    activity_id: str
    description: str
    discipline: str
    location: Optional[str]
    equipment_id: Optional[str]
    current_actual_progress: float
    current_status: str
    scores: MatchComponentScores
    rank: int
    confidence_tier: str
    rationale: str
    contradictions: Optional[str] = None

class EventMatchesResponse(BaseModel):
    event: FieldEventResponse
    source_document: Optional[DocumentResponse] = None
    top_candidates: List[MatchCandidate]
    confidence_tier: str
    recommended_activity_id: Optional[str] = None
    decision: str = "PENDING"
    match_id: Optional[str] = None

# Governance & Decision Schemas
class ApproveMatchRequest(BaseModel):
    decided_by: str = "Chief Planner"
    notes: Optional[str] = None

class EditMatchRequest(BaseModel):
    override_activity_id: str
    new_progress_percent: Optional[float] = None
    new_actual_quantity: Optional[float] = None
    new_status: Optional[str] = None
    decided_by: str = "Chief Planner"
    notes: Optional[str] = None

class RejectMatchRequest(BaseModel):
    decided_by: str = "Chief Planner"
    reason: str

# Audit Log Schema
class AuditLogResponse(BaseModel):
    id: str
    event_id: str
    document_id: Optional[str] = None
    match_id: Optional[str] = None
    ai_top_activity_id: Optional[str] = None
    ai_score: Optional[float] = None
    ai_confidence: Optional[str] = None
    action: str
    final_activity_id: Optional[str] = None
    previous_state: Optional[Dict[str, Any]] = None
    resulting_state: Optional[Dict[str, Any]] = None
    actor: str
    timestamp: datetime
    notes: Optional[str] = None
    class Config:
        from_attributes = True

# Dashboard Summary Schema
class DashboardSummaryResponse(BaseModel):
    project_id: str
    project_name: str
    planned_progress: float
    actual_progress: float
    schedule_variance: float
    total_activities: int
    completed_activities: int
    in_progress_activities: int
    not_started_activities: int
    delayed_activities: int
    total_events: int
    pending_reviews: int
    high_confidence_matches: int
    medium_confidence_matches: int
    low_confidence_matches: int
    unmatched_count: int
    recent_approved_updates: List[AuditLogResponse]
    planned_vs_actual_curve: List[Dict[str, Any]]
