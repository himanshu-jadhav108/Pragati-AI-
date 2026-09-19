# InfraNexus AI — 3 to 5 Minute SIH Judge Demo Script

**Team:** InfraNexus  
**Project:** InfraNexus AI  
**Problem Statement:** SIH26122 (Oil India Limited)  
**URL:** [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Pre-Demo Quick Check
Ensure the server is running:
```powershell
python run.py
```
Open browser to `http://127.0.0.1:8000`.

---

## 1. Executive Dashboard (0:00 - 0:45)
- **What to say:**
  > *"InfraNexus AI is the intelligence and governance bridge between unstructured daily field execution reports (DPRs) and detailed L5/L6 project schedules for Oil India's infrastructure projects. Planners traditionally spend hours manually mapping fragmented field text to hundreds of WBS codes. Our system automates this translation while enforcing human planner control."*
- **What to show on screen:**
  - **Planned vs Actual Progress:** Show the current planned progress (68.5%) vs actual progress (54.2%) and negative schedule variance (-14.3%).
  - **S-Curve Chart:** Point to the real-time S-curve comparing approved baseline vs actual progress.
  - **Status Cards:** Show Pending Reviews and Unmatched events.

---

## 2. Ingestion & Hero Case Matching (0:45 - 2:00)
- **What to say:**
  > *"Let's simulate a site engineer submitting a daily progress report for the Duliajan-Numaligarh pipeline project. Notice that field terminology rarely matches schedule activity descriptions word-for-word."*
- **Action:**
  1. Click **"📥 Field DPR Ingestion"** tab.
  2. Click **"🌟 Hero Case"** quick button (loads `DPR-OIL-2026-0308-01.txt`).
  3. Show the raw DPR text containing:
     > *"Spool erection near V-105 completed today. 14 spools installed."*
  4. Click **"🚀 Run Structured Event Extraction & Matching"**.
- **What happens:**
  - AI extraction parses:
    - Activity: Erection / Spool
    - Location: `V-105`
    - Equipment: `V-105`
    - Quantity: `14 spools`
    - Status: `COMPLETED`
  - System redirects to the **"Planner Review Queue"**.

---

## 2.5. Time Agent: Conversational Field Logging (2:00 - 2:30)
- **What to say:**
  > *"Site supervisors in remote pipeline trenches often don't have the time to draft formal DPR documents. We built Time Agent — a conversational mobile-friendly logging interface that lets supervisors speak or type field progress naturally."*
- **Action:**
  1. Click **"💬 Time Agent"** tab.
  2. Click the quick-reply demo button: **"Foundation concrete at PH-2"** (or type: *"Foundation concrete poured at Pump House PH-2"*).
  3. **Show what happens:**
     - AI parses engineering facts: Discipline (`Civil`), Location (`Pump House PH-2`), Status (`IN_PROGRESS`).
     - Matches against baseline schedule with confidence tier and score badge.
     - Instant confirmation message: *"Logged: Foundation concrete poured at Pump House PH-2 - matched to CIV-L6-1060 (MEDIUM confidence)."*
     - Click **"Inspect in Queue &rarr;"** — proves the quick log entered the exact same human-in-the-loop review workflow!
  4. *(Optional Judge Wow Beat)*: Click **"Catering delivery at gate"** — show how Time Agent safely rejects false matches and prompts the supervisor for clarification (*"Which line or equipment ID is this near?"*).

---

## 3. Human Governance & Multi-Signal Workstation (2:30 - 3:30)
- **Action:**
  1. In the Review Queue, see the new event with **HIGH Confidence** and score ~74.5%.
  2. Click **"Inspect"** to open the **Split-Screen Planner Workstation**.
- **What to explain to the judge:**
  - **Left Pane:** Point to the yellow **Evidence Box** showing the exact grounded sentence from the DPR.
  - **Right Pane:**
    - Explain that candidate `PIP-L6-0427 — Erect Line 24-inch near V-105` ranked **#1** naturally from orthogonal signals, **not hardcoding**:
      - Semantic Similarity (50% weight): 0.49
      - Discipline Match (15% weight): 1.0 (Piping)
      - Entity / Equipment (15% weight): 1.0 (V-105)
      - Location (10% weight): 1.0 (V-105)
      - Schedule Temporal Window (10% weight): 1.0 (March 8 falls within planned window)
    - Show that Rank 2 (`PIP-L6-1001`) scored only 0.51, giving a decisive margin.
  - **Emphasize Governance:**
    > *"Notice that up to this moment, the schedule has NOT changed. The AI only proposes; the planner decides."*
  3. Click **"Approve Schedule Update"**.
- **Visible Effect:**
  - Toast: *"Update approved and committed to schedule"*.
  - Actual progress of `PIP-L6-0427` updates to 100% (COMPLETED).
  - Dashboard recalculates overall project actual progress and variance.

---

## 4. Ambiguous & Unmatched Edge Cases (3:30 - 4:15)
- **Show Ambiguous Case:**
  - In Review Queue, filter by **"Medium (Review)"**.
  - Open inspection on *"Suction line welding in progress at Pump House PH-1..."*
  - Show that two activities (`PIP-L6-0501` at Pump P-101A and `PIP-L6-0502` at Pump P-101B) are in a virtual tie (margin < 0.08).
  - Show how the system **downgraded the confidence to MEDIUM** and flags that human review is strictly required.
  - Click **"Edit & Approve"** &rarr; select candidate P-101B &rarr; commit.
- **Show Unmatched Case:**
  - Filter by **"Unmatched"**.
  - Show *"Catering supply van arrived at main gate 3..."*
  - The system scores it ~0.0% and tags it **UNMATCHED**.
  - No schedule mutation occurs.

---

## 5. Audit Trail & Institutional Memory (4:15 - 5:00)
- **Audit Trail Beat (4:15 - 4:40):**
  1. Click **"📜 Governance Audit Trail"** tab.
  2. Point to the complete, immutable audit record showing:
     - Event ID & Source Document
     - AI Top Suggestion & Score
     - Planner Action (`APPROVE` or `EDIT_APPROVE`)
     - State Diff: `0% -> 100%`
     - Decided By: Chief Planner & Timestamp
- **Institutional Memory Beat (4:40 - 5:00):**
  1. Click **"📚 Institutional Memory"** tab.
  2. **What to say:**
     > *"Every approved update builds Oil India's Institutional Memory — a growing, queryable history of what actually happened, eliminating repetitive schedule optimism for future capital projects."*
  3. **What to show on screen:**
     - **Summary Cards:** 56 completed baseline activities analyzed, total overrun count vs on-time, and average schedule variance.
     - **Discipline Delay Impact Cards:** Automatically sorted by the disciplines experiencing the greatest cumulative delay impact.
     - **Execution Log Table:** Planned vs actual durations and color-coded variance (green for on-time/ahead, red for overrun).
     - Filter by discipline (e.g. `Piping` or `Civil`) to demonstrate instant historical benchmarking for future project baselining.
  4. (Optional) Show **"Demo Reset"** in **⚙️ System Health** tab to reset the entire database to baseline state in one click.
