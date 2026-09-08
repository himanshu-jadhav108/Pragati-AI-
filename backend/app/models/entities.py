import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, Boolean
)
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(String(20), nullable=True)
    finish_date = Column(String(20), nullable=True)
    planned_progress = Column(Float, default=0.0)
    actual_progress = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    activities = relationship("Activity", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")


class WBSNode(Base):
    __tablename__ = "wbs_nodes"

    wbs_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    level = Column(Integer, nullable=False)
    parent_id = Column(String(50), ForeignKey("wbs_nodes.wbs_id"), nullable=True)

    parent = relationship("WBSNode", remote_side=[wbs_id], backref="children")
    activities = relationship("Activity", back_populates="wbs_node")


class Activity(Base):
    __tablename__ = "activities"

    activity_id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("projects.id"), default="OIL-DNPE-2026")
    wbs_id = Column(String(50), ForeignKey("wbs_nodes.wbs_id"), nullable=True)
    description = Column(Text, nullable=False)
    discipline = Column(String(50), nullable=False)
    location = Column(String(100), nullable=True)
    equipment_id = Column(String(100), nullable=True)
    
    planned_start = Column(String(20), nullable=True)
    planned_finish = Column(String(20), nullable=True)
    planned_progress = Column(Float, default=0.0)
    
    actual_start = Column(String(20), nullable=True)
    actual_finish = Column(String(20), nullable=True)
    actual_progress = Column(Float, default=0.0)
    
    target_quantity = Column(Float, default=0.0)
    actual_quantity = Column(Float, default=0.0)
    unit = Column(String(50), nullable=True)
    status = Column(String(50), default="NOT_STARTED")  # NOT_STARTED, IN_PROGRESS, COMPLETED, DELAYED
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="activities")
    wbs_node = relationship("WBSNode", back_populates="activities")
    progress_updates = relationship("ProgressUpdate", back_populates="activity")
    matches = relationship("Match", back_populates="candidate_activity")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    project_id = Column(String(50), ForeignKey("projects.id"), default="OIL-DNPE-2026")
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # txt, pdf, csv
    file_size = Column(Integer, default=0)
    raw_text = Column(Text, nullable=True)
    uploaded_by = Column(String(100), default="Site Engineer")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="documents")
    events = relationship("FieldEvent", back_populates="document", cascade="all, delete-orphan")


class FieldEvent(Base):
    __tablename__ = "field_events"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    document_id = Column(String(50), ForeignKey("documents.id"), nullable=False)
    raw_text = Column(Text, nullable=False)
    event_date = Column(String(20), nullable=True)
    discipline = Column(String(50), nullable=True)
    activity_description = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    equipment_id = Column(String(100), nullable=True)
    status = Column(String(50), nullable=True)
    progress_percent = Column(Float, nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    evidence_text = Column(Text, nullable=True)
    extraction_provider = Column(String(50), default="fallback")
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="events")
    matches = relationship("Match", back_populates="event", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    event_id = Column(String(50), ForeignKey("field_events.id"), nullable=False)
    activity_id = Column(String(50), ForeignKey("activities.activity_id"), nullable=True)
    
    # Detailed scoring breakdown
    score_semantic = Column(Float, default=0.0)
    score_discipline = Column(Float, default=0.0)
    score_entity = Column(Float, default=0.0)
    score_location = Column(Float, default=0.0)
    score_temporal = Column(Float, default=0.0)
    penalty_contradiction = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    
    rank = Column(Integer, default=1)
    confidence_tier = Column(String(20), default="LOW")  # HIGH, MEDIUM, LOW, UNMATCHED
    rationale = Column(Text, nullable=True)
    contradictions = Column(Text, nullable=True)
    
    # Review & Governance
    decision = Column(String(30), default="PENDING")  # PENDING, APPROVED, REJECTED, EDITED, UNMATCHED
    decided_by = Column(String(100), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decision_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("FieldEvent", back_populates="matches")
    candidate_activity = relationship("Activity", back_populates="matches")
    audit_logs = relationship("AuditLog", back_populates="match")


class ProgressUpdate(Base):
    __tablename__ = "progress_updates"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    activity_id = Column(String(50), ForeignKey("activities.activity_id"), nullable=False)
    event_id = Column(String(50), ForeignKey("field_events.id"), nullable=False)
    match_id = Column(String(50), ForeignKey("matches.id"), nullable=False)
    
    before_progress = Column(Float, default=0.0)
    after_progress = Column(Float, default=0.0)
    before_quantity = Column(Float, default=0.0)
    after_quantity = Column(Float, default=0.0)
    before_status = Column(String(50), nullable=True)
    after_status = Column(String(50), nullable=True)
    
    applied_by = Column(String(100), default="Planner")
    applied_at = Column(DateTime, default=datetime.utcnow)

    activity = relationship("Activity", back_populates="progress_updates")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    event_id = Column(String(50), nullable=False)
    document_id = Column(String(50), nullable=True)
    match_id = Column(String(50), ForeignKey("matches.id"), nullable=True)
    
    ai_top_activity_id = Column(String(50), nullable=True)
    ai_score = Column(Float, nullable=True)
    ai_confidence = Column(String(20), nullable=True)
    
    action = Column(String(50), nullable=False)  # APPROVE, EDIT_APPROVE, REJECT, MARK_UNMATCHED
    final_activity_id = Column(String(50), nullable=True)
    previous_state = Column(JSON, nullable=True)
    resulting_state = Column(JSON, nullable=True)
    
    actor = Column(String(100), default="Chief Planner")
    timestamp = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    match = relationship("Match", back_populates="audit_logs")


class DelayEvent(Base):
    __tablename__ = "delay_events"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    activity_id = Column(String(50), ForeignKey("activities.activity_id"), nullable=False)
    delay_reason = Column(String(255), nullable=False)
    delay_days = Column(Integer, default=0)
    logged_at = Column(DateTime, default=datetime.utcnow)
