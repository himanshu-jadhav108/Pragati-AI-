import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from backend.app.models.entities import Activity, FieldEvent, Match
from backend.app.schemas.schemas import MatchCandidate, MatchComponentScores, EventMatchesResponse
from backend.app.core.config import settings

class SemanticScorer:
    """
    Local TF-IDF & Cosine Similarity Semantic Scorer.
    Offline-ready, deterministic, highly accurate on domain terms.
    """
    def __init__(self, corpus: List[str]):
        # Domain stop words and construction ngram analyzer
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b[A-Za-z0-9\-_]+\b",
            lowercase=True
        )
        if corpus:
            self.activity_matrix = self.vectorizer.fit_transform(corpus)
        else:
            self.activity_matrix = None

    def compute_similarity(self, query_text: str) -> np.ndarray:
        if self.activity_matrix is None or not query_text.strip():
            return np.zeros(self.activity_matrix.shape[0] if self.activity_matrix is not None else 0)
        query_vec = self.vectorizer.transform([query_text])
        sim = cosine_similarity(query_vec, self.activity_matrix)[0]
        return np.clip(sim, 0.0, 1.0)


class MatchingEngine:
    def __init__(self, db: Session, project_id: str = "OIL-DNPE-2026"):
        self.db = db
        self.project_id = project_id
        # Preload activities for project
        self.activities: List[Activity] = (
            db.query(Activity)
            .filter(Activity.project_id == project_id)
            .all()
        )
        
        # Build corpus of activity text
        # Combine description + discipline + location + equipment + WBS for rich semantic context
        corpus = []
        for act in self.activities:
            text = f"{act.description} {act.discipline} {act.location or ''} {act.equipment_id or ''}"
            corpus.append(text)
            
        self.semantic_scorer = SemanticScorer(corpus)

    def _normalize(self, text: Optional[str]) -> str:
        if not text:
            return ""
        return re.sub(r"[^a-zA-Z0-9]", "", text).lower()

    def _calculate_discipline_score(self, event_disc: Optional[str], act_disc: str) -> float:
        if not event_disc:
            return 0.5  # Neutral / unknown
        if self._normalize(event_disc) == self._normalize(act_disc):
            return 1.0
        # Compatible disciplines
        compatible_pairs = [
            ("piping", "mechanical"),
            ("electrical", "instrumentation"),
            ("civil", "hse")
        ]
        norm_e = self._normalize(event_disc)
        norm_a = self._normalize(act_disc)
        for d1, d2 in compatible_pairs:
            if (norm_e == d1 and norm_a == d2) or (norm_e == d2 and norm_a == d1):
                return 0.4
        return 0.0  # Mismatch

    def _calculate_entity_score(self, event_eq: Optional[str], act_eq: Optional[str], event_text: str) -> float:
        norm_act_eq = self._normalize(act_eq)
        if not norm_act_eq:
            return 0.3  # Activity has no specific tag
            
        # Check explicit equipment_id extracted
        if event_eq and self._normalize(event_eq) == norm_act_eq:
            return 1.0
            
        # Check if activity equipment appears anywhere in event text
        if act_eq and act_eq.lower() in event_text.lower():
            return 1.0
            
        return 0.0

    def _calculate_location_score(self, event_loc: Optional[str], act_loc: Optional[str], event_text: str) -> float:
        norm_act_loc = self._normalize(act_loc)
        if not norm_act_loc:
            return 0.3  # Activity has no specific location tag
            
        if event_loc and self._normalize(event_loc) == norm_act_loc:
            return 1.0
            
        if act_loc and act_loc.lower() in event_text.lower():
            return 1.0
            
        # Partial match (e.g. "Pump House" in "Pump House PH-1")
        if event_loc and act_loc:
            if event_loc.lower() in act_loc.lower() or act_loc.lower() in event_loc.lower():
                return 0.7
                
        return 0.0

    def _calculate_temporal_score(self, event_date_str: Optional[str], p_start_str: Optional[str], p_finish_str: Optional[str]) -> float:
        if not event_date_str or not p_start_str or not p_finish_str:
            return 0.5  # Soft default
            
        try:
            event_date = datetime.strptime(event_date_str[:10], "%Y-%m-%d")
            p_start = datetime.strptime(p_start_str[:10], "%Y-%m-%d")
            p_finish = datetime.strptime(p_finish_str[:10], "%Y-%m-%d")
            
            # If within planned window
            if p_start <= event_date <= p_finish:
                return 1.0
            # If within 15 days of window
            days_before = (p_start - event_date).days
            days_after = (event_date - p_finish).days
            if 0 < days_after <= 30:
                return 0.8  # Real reports often come slightly late
            if 0 < days_before <= 14:
                return 0.7  # Work started early
            return 0.4
        except Exception:
            return 0.5

    def _detect_contradictions(self, event: FieldEvent, act: Activity) -> Tuple[float, Optional[str]]:
        penalty = 0.0
        contradiction_reasons = []

        # 1. Location clash: both have explicitly conflicting locations
        if event.location and act.location:
            e_loc = event.location.strip().lower()
            a_loc = act.location.strip().lower()
            if e_loc != a_loc and (e_loc not in a_loc and a_loc not in e_loc):
                penalty += 0.35
                contradiction_reasons.append(f"Location conflict: Event at '{event.location}' vs Activity at '{act.location}'")

        # 2. Discipline clash: severe mismatch (e.g. Civil vs Electrical)
        if event.discipline and act.discipline:
            if self._calculate_discipline_score(event.discipline, act.discipline) == 0.0:
                penalty += 0.30
                contradiction_reasons.append(f"Discipline conflict: Event is '{event.discipline}' vs Activity is '{act.discipline}'")

        # 3. Work type clash: Fabrication vs Field Erection
        raw = (getattr(event, "raw_text", None) or getattr(event, "evidence_text", "") or "").lower()
        desc = act.description.lower()
        if ("erection" in raw or "installed" in raw) and "shop fabrication" in desc:
            penalty += 0.40
            contradiction_reasons.append("Type conflict: Field erection reported for shop fabrication activity")

        reason_str = "; ".join(contradiction_reasons) if contradiction_reasons else None
        return penalty, reason_str

    def score_event(self, event: Any, top_k: int = 5) -> Tuple[List[MatchCandidate], str]:
        if not self.activities:
            return [], "UNMATCHED"

        event_text = getattr(event, "raw_text", None) or getattr(event, "evidence_text", "") or ""

        # Compute semantic similarities for all activities
        query = f"{event.activity_description or ''} {event.discipline or ''} {event.location or ''} {event.evidence_text or ''}"
        semantic_sims = self.semantic_scorer.compute_similarity(query)

        candidates: List[MatchCandidate] = []

        w_sem = settings.WEIGHT_SEMANTIC
        w_disc = settings.WEIGHT_DISCIPLINE
        w_ent = settings.WEIGHT_ENTITY
        w_loc = settings.WEIGHT_LOCATION
        w_temp = settings.WEIGHT_TEMPORAL

        for idx, act in enumerate(self.activities):
            s_sem = float(semantic_sims[idx])
            s_disc = self._calculate_discipline_score(event.discipline, act.discipline)
            s_ent = self._calculate_entity_score(event.equipment_id, act.equipment_id, event_text)
            s_loc = self._calculate_location_score(event.location, act.location, event_text)
            s_temp = self._calculate_temporal_score(event.event_date, act.planned_start, act.planned_finish)
            
            penalty, contradictions = self._detect_contradictions(event, act)

            # Baseline weighted formula
            raw_score = (
                (w_sem * s_sem) +
                (w_disc * s_disc) +
                (w_ent * s_ent) +
                (w_loc * s_loc) +
                (w_temp * s_temp)
            )
            final_score = max(0.0, min(1.0, raw_score - penalty))

            # Generate rationale
            rationale_parts = []
            if s_sem >= 0.4:
                rationale_parts.append(f"Strong semantic overlap ({s_sem:.2f})")
            if s_loc >= 0.9:
                rationale_parts.append(f"Matched location '{act.location}'")
            if s_ent >= 0.9:
                rationale_parts.append(f"Matched equipment '{act.equipment_id}'")
            if s_disc >= 0.9:
                rationale_parts.append(f"Matched discipline '{act.discipline}'")
            if s_temp >= 0.8:
                rationale_parts.append("Aligned with planned schedule window")
            
            rationale = ", ".join(rationale_parts) if rationale_parts else "Weak contextual correlation"

            scores = MatchComponentScores(
                score_semantic=round(s_sem, 3),
                score_discipline=round(s_disc, 3),
                score_entity=round(s_ent, 3),
                score_location=round(s_loc, 3),
                score_temporal=round(s_temp, 3),
                penalty_contradiction=round(penalty, 3),
                final_score=round(final_score, 3)
            )

            candidates.append(MatchCandidate(
                activity_id=act.activity_id,
                description=act.description,
                discipline=act.discipline,
                location=act.location,
                equipment_id=act.equipment_id,
                current_actual_progress=act.actual_progress,
                current_status=act.status,
                scores=scores,
                rank=1,
                confidence_tier="LOW",
                rationale=rationale,
                contradictions=contradictions
            ))

        # Sort candidates descending by final_score
        candidates.sort(key=lambda c: c.scores.final_score, reverse=True)
        top_candidates = candidates[:top_k]

        # Assign ranks
        for r_idx, c in enumerate(top_candidates):
            c.rank = r_idx + 1

        # Determine overall confidence tier
        if not top_candidates or top_candidates[0].scores.final_score < settings.THRESHOLD_UNMATCHED:
            overall_confidence = "UNMATCHED"
            for c in top_candidates:
                c.confidence_tier = "UNMATCHED"
        else:
            rank1 = top_candidates[0]
            rank2_score = top_candidates[1].scores.final_score if len(top_candidates) > 1 else 0.0
            margin = rank1.scores.final_score - rank2_score

            has_corroborating = (
                rank1.scores.score_location >= 0.7 or
                rank1.scores.score_entity >= 0.7 or
                rank1.scores.score_discipline >= 0.9
            )

            # Confidence policy from prompt 06
            if (rank1.scores.final_score >= settings.THRESHOLD_HIGH and
                has_corroborating and
                margin >= settings.MARGIN_HIGH_CONFIDENCE):
                overall_confidence = "HIGH"
                rank1.confidence_tier = "HIGH"
            elif rank1.scores.final_score >= settings.THRESHOLD_MEDIUM:
                overall_confidence = "MEDIUM"
                rank1.confidence_tier = "MEDIUM"
            else:
                overall_confidence = "LOW"
                rank1.confidence_tier = "LOW"

            # Check for close competition downgrade (Ambiguous case)
            if overall_confidence == "HIGH" and margin < settings.MARGIN_HIGH_CONFIDENCE:
                overall_confidence = "MEDIUM"
                rank1.confidence_tier = "MEDIUM"
                rank1.rationale += f" [Confidence adjusted to MEDIUM: close margin {margin:.2f} with rank 2]"

        return top_candidates, overall_confidence

    def process_and_persist_matches(self, event: FieldEvent) -> EventMatchesResponse:
        top_candidates, overall_confidence = self.score_event(event, top_k=5)

        # Clear existing unapproved matches for this event
        self.db.query(Match).filter(
            Match.event_id == event.id,
            Match.decision == "PENDING"
        ).delete()

        recommended_id = None
        top_match_id = None

        if overall_confidence != "UNMATCHED" and top_candidates:
            recommended_id = top_candidates[0].activity_id

        # Persist candidate records in DB
        for c in top_candidates:
            m = Match(
                event_id=event.id,
                activity_id=c.activity_id,
                score_semantic=c.scores.score_semantic,
                score_discipline=c.scores.score_discipline,
                score_entity=c.scores.score_entity,
                score_location=c.scores.score_location,
                score_temporal=c.scores.score_temporal,
                penalty_contradiction=c.scores.penalty_contradiction,
                final_score=c.scores.final_score,
                rank=c.rank,
                confidence_tier=overall_confidence if c.rank == 1 else "LOW",
                rationale=c.rationale,
                contradictions=c.contradictions,
                decision="UNMATCHED" if overall_confidence == "UNMATCHED" else "PENDING"
            )
            self.db.add(m)
            self.db.flush()
            if c.rank == 1:
                top_match_id = m.id

        event.is_processed = True
        self.db.commit()

        # Build response schema
        from backend.app.schemas.schemas import FieldEventResponse, DocumentResponse
        event_resp = FieldEventResponse.from_orm(event)
        doc_resp = DocumentResponse.from_orm(event.document) if event.document else None

        return EventMatchesResponse(
            event=event_resp,
            source_document=doc_resp,
            top_candidates=top_candidates,
            confidence_tier=overall_confidence,
            recommended_activity_id=recommended_id,
            decision="UNMATCHED" if overall_confidence == "UNMATCHED" else "PENDING",
            match_id=top_match_id
        )
