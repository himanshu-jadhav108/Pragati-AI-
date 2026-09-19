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

    def _filter_contextual_candidates(self, event: Any) -> List[Tuple[int, Activity]]:
        """
        Lightweight candidate pre-filtering pipeline:
        ALL SCHEDULE ACTIVITIES -> CONTEXTUAL CANDIDATES -> (Fallback to all if too narrow)
        """
        if not self.activities:
            return []

        event_text = (getattr(event, "raw_text", None) or getattr(event, "evidence_text", "") or "").lower()
        event_disc = (getattr(event, "discipline", None) or "").lower()
        event_loc = (getattr(event, "location", None) or "").lower()
        event_eq = (getattr(event, "equipment_id", None) or "").lower()

        contextual = []
        for idx, act in enumerate(self.activities):
            act_disc = (act.discipline or "").lower()
            act_loc = (act.location or "").lower()
            act_eq = (act.equipment_id or "").lower()
            act_desc = (act.description or "").lower()

            # Signals
            disc_match = bool(event_disc and (event_disc == act_disc or self._calculate_discipline_score(event_disc, act_disc) > 0.3))
            loc_match = bool(event_loc and (event_loc in act_loc or act_loc in event_loc or act_loc in event_text))
            eq_match = bool(event_eq and (event_eq in act_eq or act_eq in event_text))
            
            # Key activity token overlap
            tokens = [t for t in re.findall(r"\b[a-z0-9\-]+\b", event_text) if len(t) > 3 and t not in {"today", "yesterday", "completed", "installed", "ongoing", "started", "area"}]
            token_match = any(t in act_desc for t in tokens)

            if disc_match or loc_match or eq_match or token_match:
                contextual.append((idx, act))

        # Fallback to all activities if filtering would make candidate pool too small
        if len(contextual) < 5:
            return list(enumerate(self.activities))
        return contextual

    def _generate_why_matched(self, event: Any, act: Activity, scores: MatchComponentScores, event_text: str) -> List[str]:
        """
        Generates truthful, factual evidence checklist for 'Why This Match?'.
        Only displays checkmarks where the evidence signal actually contributed.
        """
        signals: List[str] = []
        act_desc = act.description.lower()
        ev_text_low = event_text.lower()

        # 1. Discipline signal
        if scores.score_discipline >= 0.9:
            signals.append(f"✓ {act.discipline} discipline matched")
        elif scores.score_discipline >= 0.4:
            signals.append(f"✓ Compatible discipline ({act.discipline})")
        elif getattr(event, "discipline", None):
            signals.append(f"⚠ Discipline mismatch ({act.discipline})")

        # 2. Location signal
        if scores.score_location >= 0.7:
            loc_name = act.location or getattr(event, "location", "")
            signals.append(f"✓ {loc_name} location confirmed")
        elif getattr(event, "location", None) or act.location:
            signals.append("⚠ Location not confirmed")

        # 3. Equipment / Asset signal
        if scores.score_entity >= 0.7:
            eq_name = act.equipment_id or getattr(event, "equipment_id", "")
            signals.append(f"✓ {eq_name} attribute/asset matched")
        elif getattr(event, "equipment_id", None) and act.equipment_id:
            signals.append("⚠ Asset unverified")

        # 4. Contextual size / line attribute
        for attr in ["24-inch", "24\"", "14-inch", "14\"", "18-inch", "12-inch", "suction", "discharge", "booster"]:
            if attr in ev_text_low and (attr in act_desc or (attr == "24\"" and "24-inch" in act_desc)):
                clean_attr = attr.replace('"', '-inch')
                signals.append(f"✓ {clean_attr} attribute")
                break

        # 5. Engineering Activity verb
        action_verbs = [
            ("erect", "Erection activity"),
            ("weld", "Welding activity"),
            ("pour", "Concrete pour activity"),
            ("concrete", "Civil concrete activity"),
            ("excavat", "Excavation activity"),
            ("hydrotest", "Hydrotest activity"),
            ("align", "Alignment activity"),
            ("cable", "Cable installation activity"),
            ("loop", "Loop check activity"),
            ("install", "Installation activity")
        ]
        for stem, label in action_verbs:
            if stem in ev_text_low and stem in act_desc:
                signals.append(f"✓ {label}")
                break

        # 6. Schedule Temporal Context
        if scores.score_temporal >= 0.8:
            signals.append("✓ Schedule context aligned")
        else:
            signals.append("⚠ Outside planned schedule window")

        # 7. Semantic text similarity
        if scores.score_semantic >= 0.45:
            signals.append(f"✓ Strong text similarity ({scores.score_semantic:.2f})")
        elif scores.score_semantic >= 0.25:
            signals.append(f"✓ Moderate text similarity ({scores.score_semantic:.2f})")
        else:
            signals.append("⚠ Low text similarity")

        # 8. Contradictions
        if scores.penalty_contradiction > 0:
            signals.append(f"⚠ Contradiction penalty (-{scores.penalty_contradiction:.2f})")

        return signals

    def score_event(self, event: Any, top_k: int = 5) -> Tuple[List[MatchCandidate], str]:
        if not self.activities:
            return [], "UNMATCHED"

        event_text = getattr(event, "raw_text", None) or getattr(event, "evidence_text", "") or ""

        # Compute semantic similarities for all activities
        query = f"{event.activity_description or ''} {event.discipline or ''} {event.location or ''} {event.evidence_text or ''}"
        semantic_sims = self.semantic_scorer.compute_similarity(query)

        # Candidate filtering: ALL ACTIVITIES -> CONTEXTUAL CANDIDATES
        contextual_candidates = self._filter_contextual_candidates(event)

        candidates: List[MatchCandidate] = []

        w_sem = settings.WEIGHT_SEMANTIC
        w_disc = settings.WEIGHT_DISCIPLINE
        w_ent = settings.WEIGHT_ENTITY
        w_loc = settings.WEIGHT_LOCATION
        w_temp = settings.WEIGHT_TEMPORAL

        for idx, act in contextual_candidates:
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

            scores = MatchComponentScores(
                score_semantic=round(s_sem, 3),
                score_discipline=round(s_disc, 3),
                score_entity=round(s_ent, 3),
                score_location=round(s_loc, 3),
                score_temporal=round(s_temp, 3),
                penalty_contradiction=round(penalty, 3),
                final_score=round(final_score, 3)
            )

            why_matched = self._generate_why_matched(event, act, scores, event_text)
            rationale = "; ".join([s for s in why_matched if s.startswith("✓")]) or "Weak contextual correlation"

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
                contradictions=contradictions,
                why_matched=why_matched
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

            # Prototype routing thresholds
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

            # Ambiguous close competition downgrade: routes to MEDIUM (Planner Review Required)
            if overall_confidence == "HIGH" and margin < settings.MARGIN_HIGH_CONFIDENCE:
                overall_confidence = "MEDIUM"
                rank1.confidence_tier = "MEDIUM"
                rank1.rationale += f" [Close competitor within margin {margin:.2f} — Planner Review Required]"

        return top_candidates, overall_confidence

    def get_stored_matches(self, event: FieldEvent) -> Optional[EventMatchesResponse]:
        """
        Read-only retrieval of existing match records.
        Does NOT delete, recreate, or mutate database state.
        """
        existing_matches = (
            self.db.query(Match)
            .filter(Match.event_id == event.id)
            .order_by(Match.rank.asc())
            .all()
        )
        if not existing_matches:
            return None

        from backend.app.schemas.schemas import FieldEventResponse, DocumentResponse
        event_resp = FieldEventResponse.model_validate(event)
        doc_resp = DocumentResponse.model_validate(event.document) if event.document else None

        candidates = []
        overall_conf = existing_matches[0].confidence_tier if existing_matches else "UNMATCHED"
        rec_id = existing_matches[0].activity_id if existing_matches and overall_conf != "UNMATCHED" else None
        top_score = existing_matches[0].final_score if existing_matches else 0.0

        for m in existing_matches:
            act = m.candidate_activity
            scores = MatchComponentScores(
                score_semantic=m.score_semantic,
                score_discipline=m.score_discipline,
                score_entity=m.score_entity,
                score_location=m.score_location,
                score_temporal=m.score_temporal,
                penalty_contradiction=m.penalty_contradiction,
                final_score=m.final_score
            )
            why_matched = []
            if m.rationale:
                # Reconstruct checklist
                why_matched = [s.strip() for s in m.rationale.split(";") if s.strip()]
            if act:
                why_matched = self._generate_why_matched(event, act, scores, event.raw_text or event.evidence_text or "")

            candidates.append(MatchCandidate(
                activity_id=m.activity_id or "NONE",
                description=act.description if act else "No activity assigned",
                discipline=act.discipline if act else "Unknown",
                location=act.location if act else None,
                equipment_id=act.equipment_id if act else None,
                current_actual_progress=act.actual_progress if act else 0.0,
                current_status=act.status if act else "NOT_STARTED",
                scores=scores,
                rank=m.rank,
                confidence_tier=m.confidence_tier,
                rationale=m.rationale or "",
                contradictions=m.contradictions,
                why_matched=why_matched
            ))

        return EventMatchesResponse(
            event=event_resp,
            source_document=doc_resp,
            top_candidates=candidates,
            confidence_tier=overall_conf,
            match_score=round(top_score, 3),
            recommended_activity_id=rec_id,
            decision=existing_matches[0].decision if existing_matches else "PENDING",
            match_id=existing_matches[0].id if existing_matches else None
        )

    def process_and_persist_matches(self, event: FieldEvent) -> EventMatchesResponse:
        """
        Executes matching computation and persists new candidate records in the database.
        Called on event creation or explicit recomputation.
        """
        top_candidates, overall_confidence = self.score_event(event, top_k=5)

        # Clear existing unapproved matches for this event
        self.db.query(Match).filter(
            Match.event_id == event.id,
            Match.decision.in_(["PENDING", "UNMATCHED"])
        ).delete()

        recommended_id = None
        top_match_id = None

        if overall_confidence != "UNMATCHED" and top_candidates:
            recommended_id = top_candidates[0].activity_id

        # Persist candidate records in DB
        for c in top_candidates:
            rationale_text = "; ".join(c.why_matched) if c.why_matched else c.rationale
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
                rationale=rationale_text,
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
        event_resp = FieldEventResponse.model_validate(event)
        doc_resp = DocumentResponse.model_validate(event.document) if event.document else None
        top_score = top_candidates[0].scores.final_score if top_candidates else 0.0

        return EventMatchesResponse(
            event=event_resp,
            source_document=doc_resp,
            top_candidates=top_candidates,
            confidence_tier=overall_confidence,
            match_score=round(top_score, 3),
            recommended_activity_id=recommended_id,
            decision="UNMATCHED" if overall_confidence == "UNMATCHED" else "PENDING",
            match_id=top_match_id
        )

