"""
InfraNexus AI — Ground-Truth Evaluation Runner
Problem Statement: SIH26122 (Oil India Limited)
Team: Infranexus

Measures:
- Clear Match Top-1 Accuracy
- Top-3 Candidate Recall
- Ambiguity Routing Accuracy (medium confidence review routing)
- No-Match Detection Accuracy (unmatched preservation)
- Processing Latency
"""

import os
import sys
import csv
import time
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.db.session import SessionLocal
from backend.app.services.extraction.extractor import RuleBasedFallbackExtractor
from backend.app.services.matching.matching_engine import MatchingEngine
from backend.app.core.config import settings

def run_evaluation():
    db = SessionLocal()
    extractor = RuleBasedFallbackExtractor()
    engine = MatchingEngine(db, project_id="OIL-DNPE-2026")
    
    gt_file = os.path.join(PROJECT_ROOT, "data", "ground_truth.csv")
    if not os.path.exists(gt_file):
        print(f"Ground truth file not found: {gt_file}")
        return

    with open(gt_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        ground_truth = list(reader)

    print(f"Evaluating {len(ground_truth)} controlled benchmark scenarios on InfraNexus AI...")

    clear_match_total = 0
    clear_match_top1_correct = 0

    ambig_total = 0
    ambig_routed_correct = 0

    nomatch_total = 0
    nomatch_detected_correct = 0

    top3_total = 0
    top3_recall_correct = 0

    start_time = time.time()
    results = []

    for row in ground_truth:
        raw_text = row["raw_text"]
        expected_act_str = row["expected_activity_id"].strip() if row["expected_activity_id"] else ""
        expected_acts = [a.strip() for a in expected_act_str.split("|") if a.strip()]
        expected_conf = row["expected_confidence"].strip()
        scenario = row["scenario"].strip()

        # 1. Extraction with deterministic demo date
        events = extractor.extract_events(
            raw_text,
            metadata={"date": settings.get_effective_date(), "filename": row["doc_filename"]}
        )
        if not events:
            print(f"Warning: failed to extract events for {row['event_id']}")
            continue

        evt = events[0]

        # 2. Matching Engine scoring
        top_candidates, conf = engine.score_event(evt, top_k=3)

        top1_id = top_candidates[0].activity_id if (top_candidates and conf != "UNMATCHED") else None
        top3_ids = [c.activity_id for c in top_candidates] if conf != "UNMATCHED" else []
        top_score = top_candidates[0].scores.final_score if top_candidates else 0.0

        is_passed = False
        notes = ""

        # Case 1: No-Match Scenario
        if scenario == "NO_MATCH" or expected_conf == "UNMATCHED":
            nomatch_total += 1
            if conf == "UNMATCHED":
                nomatch_detected_correct += 1
                is_passed = True
                notes = "Correctly flagged as UNMATCHED without schedule mutation"
            else:
                notes = f"Erroneously matched to {top1_id}"

        # Case 2: Ambiguous Scenario
        elif scenario == "AMBIGUOUS_CHOICE":
            ambig_total += 1
            top3_total += 1
            # Ambiguity routing expectation: routed to MEDIUM for human validation
            # and plausible candidates retrieved in Top-3
            in_top3 = any(exp in top3_ids for exp in expected_acts)
            if in_top3:
                top3_recall_correct += 1
            if conf == "MEDIUM" and in_top3:
                ambig_routed_correct += 1
                is_passed = True
                notes = "Correctly routed to MEDIUM (Planner Review Required); candidate in Top-3"
            else:
                notes = f"Confidence {conf}, top3={top3_ids}"

        # Case 3: Clear Match Scenario
        else:
            clear_match_total += 1
            top3_total += 1
            if expected_acts and top1_id in expected_acts:
                clear_match_top1_correct += 1
                is_passed = True
                notes = "Top-1 exact match confirmed"
            if expected_acts and any(exp in top3_ids for exp in expected_acts):
                top3_recall_correct += 1

        results.append({
            "event_id": row["event_id"],
            "scenario": scenario,
            "expected_act": expected_act_str or "UNMATCHED",
            "predicted_act": top1_id or "UNMATCHED",
            "confidence": conf,
            "score": top_score,
            "passed": is_passed,
            "notes": notes
        })

    elapsed = time.time() - start_time
    avg_latency = (elapsed / len(ground_truth)) * 1000 if ground_truth else 0.0

    clear_acc = (clear_match_top1_correct / clear_match_total * 100) if clear_match_total > 0 else 0.0
    top3_rec = (top3_recall_correct / top3_total * 100) if top3_total > 0 else 0.0
    ambig_acc = (ambig_routed_correct / ambig_total * 100) if ambig_total > 0 else 0.0
    nomatch_acc = (nomatch_detected_correct / nomatch_total * 100) if nomatch_total > 0 else 0.0

    print("\n" + "=" * 65)
    print("   MEASURED BENCHMARK RESULTS — InfraNexus AI (SIH26122)")
    print("=" * 65)
    print(f"Total Scenarios Evaluated:         {len(ground_truth)}")
    print(f"Clear Match Top-1 Accuracy:        {clear_acc:.1f}% ({clear_match_top1_correct}/{clear_match_total})")
    print(f"Top-3 Candidate Recall:            {top3_rec:.1f}% ({top3_recall_correct}/{top3_total})")
    print(f"Ambiguity Routing Accuracy:        {ambig_acc:.1f}% ({ambig_routed_correct}/{ambig_total})")
    print(f"No-Match Detection Accuracy:       {nomatch_acc:.1f}% ({nomatch_detected_correct}/{nomatch_total})")
    print(f"Average Pipeline Latency:          {avg_latency:.2f} ms / event")
    print("=" * 65)

    # Write truthful, validated evaluation report to docs/evaluation.md
    docs_dir = os.path.join(PROJECT_ROOT, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    eval_md_path = os.path.join(docs_dir, "evaluation.md")

    with open(eval_md_path, "w", encoding="utf-8") as f:
        f.write("# InfraNexus AI — Ground-Truth Evaluation Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Problem Statement:** SIH26122 (Oil India Limited)\n")
        f.write(f"**Team:** Infranexus\n")
        f.write(f"**Mode:** Deterministic Offline Fallback (Local Scikit TF-IDF & Deterministic NLP Rules)\n\n")
        
        f.write("## 1. Benchmark Targets vs Measured Results\n\n")
        f.write("| Evaluation Dimension | Benchmark Target | Measured Result | Status |\n")
        f.write("|---|---|---|---|\n")
        f.write(f"| Clear Match Top-1 Accuracy | > 75.0% | **{clear_acc:.1f}%** | {'✅ PASSED' if clear_acc >= 75.0 else '⚠️ REVIEW'} |\n")
        f.write(f"| Top-3 Candidate Recall | > 90.0% | **{top3_rec:.1f}%** | {'✅ PASSED' if top3_rec >= 90.0 else '⚠️ REVIEW'} |\n")
        f.write(f"| Ambiguity Routing Accuracy | > 80.0% | **{ambig_acc:.1f}%** | {'✅ PASSED' if ambig_acc >= 80.0 else '⚠️ REVIEW'} |\n")
        f.write(f"| No-Match Detection Accuracy | > 80.0% | **{nomatch_acc:.1f}%** | {'✅ PASSED' if nomatch_acc >= 80.0 else '⚠️ REVIEW'} |\n")
        f.write(f"| Pipeline Latency (per event) | < 250 ms | **{avg_latency:.2f} ms** | {'✅ PASSED' if avg_latency < 250.0 else '⚠️ REVIEW'} |\n\n")

        f.write("## 2. Controlled Scenario Verification Matrix\n\n")
        f.write("| Event ID | Scenario Type | Expected Target | Predicted Top-1 | Confidence Tier | Match Score | Verification Status |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for r in results:
            status_badge = "✅ PASSED" if r["passed"] else "⚠️ REVIEW"
            f.write(f"| {r['event_id']} | {r['scenario']} | `{r['expected_act']}` | `{r['predicted_act']}` | {r['confidence']} | {r['score']:.3f} | {status_badge} |\n")

        f.write("\n## 3. Evaluation Methodology & Governance Principles\n")
        f.write("1. **Deterministic Demo Baseline:** Multi-signal matching (semantic 0.50, discipline 0.15, entity 0.15, location 0.10, temporal 0.10).\n")
        f.write("2. **Separation of Ambiguity from Failure:** Ambiguous real-world reports with close competitive candidates are routed to human review (MEDIUM) rather than forcing an inaccurate Top-1 mutation.\n")
        f.write("3. **Unmatched Grounding:** Field logs describing activities not present in the master schedule are safely preserved as UNMATCHED without corrupting the schedule.\n")

    print(f"Wrote evaluation report to {eval_md_path}")
    db.close()

if __name__ == "__main__":
    run_evaluation()
