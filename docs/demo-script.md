# InfraNexus AI — SIH26122 Selection-Round Judge Presentation Script

**Product:** InfraNexus AI  
**Team:** Infranexus  
**Problem Statement:** SIH26122  
**Organization:** Oil India Limited  
**Theme:** Smart Automation | Category: Software  
**Local URL:** [http://127.0.0.1:8000](http://127.0.0.1:8000)

**Product Message:**  
*“Turning field reality into schedule-linked actual progress.”*

**Core Principle:**  
`AI RECOMMENDS → EVIDENCE SUPPORTS → PLANNER VALIDATES → SYSTEM COMMITS`

---

## Pre-Presentation Quick Check
1. Start the server:
   ```powershell
   python run.py
   ```
2. Open browser to `http://127.0.0.1:8000`.
3. Confirm the top header displays:
   `DEMO MODE • Data as of 08 Mar 2026` and `AI Engine: Deterministic Fallback`.
4. If needed, click **"Reset Demo"** in the top bar to guarantee a clean baseline.

---

## 14-Step Hero Presentation Flow

### STEP 1: Executive Overview (30 seconds)
- **What to say:**
  > *"InfraNexus AI automates the critical bridge between messy, unstructured daily site observations and detailed L5/L6 project schedules for Oil India Limited. Today, field reports get stuck in silos while planners spend hours manually updating hundreds of activity codes. InfraNexus AI introduces explainable AI extraction and deterministic schedule linking — with strict human planner governance."*
- **What to show on screen:**
  - Executive Dashboard: Planned baseline vs actual progress, schedule variance, and the Primavera S-curve view.
  - Highlight the governance rule: **AI never mutates the schedule without planner validation.**

### STEP 2: Open Time Agent
- Click **"Time Agent (Capture)"** in the top navigation bar.
- Point out the conversational field logger designed for site engineers and supervisors in remote pipeline trenches.

### STEP 3: Click "High Match" Quick Demo
- Click the quick button: **`HIGH: 24-inch spool at V-105`**
- Input populates: `24-inch spool erected near V-105 today.`
- Click **Send Update**.

### STEP 4: Inspect the Canonical Progress Event
- Point to the structured **Canonical Progress Event** card inside the chat response:
  - **Discipline:** `Piping`
  - **Activity:** `Erection`
  - **Location:** `V-105`
  - **Asset / Equipment:** `Line 24-inch`
  - **Status:** `COMPLETED`
  - **Date:** `08 Mar 2026` (deterministic demo date)
- **What to say:**
  > *"Notice the transformation: Messy, natural field text is parsed into an auditable Canonical Progress Event without hallucinations."*

### STEP 5: Show the Recommended L5/L6 Activity
- Point to the matched Primavera activity banner:
  `PIP-L6-0427: Erect Line 24-inch near V-105`
- Note the confidence badge: **`HIGH CONFIDENCE`** with heuristic match score (e.g. `0.745`).

### STEP 6: Open "Why This Match?" Evidence Checklist
- Click **"Inspect in Queue →"** to enter the **Planner Review Workstation**.
- In the right-hand panel, show the **Why This Match? Supporting Evidence** checklist:
  - `✓ Piping discipline matched`
  - `✓ V-105 location confirmed`
  - `✓ 24-inch attribute match`
  - `✓ Erection activity aligned`
  - `✓ Temporal window aligned with schedule`
  - `✓ Strong text similarity (0.58)`
- Show the orthogonal score breakdown bars (Semantic, Discipline, Entity, Location, Temporal).
- Show the left-hand panel: **Source Evidence** block preserving the original field quote.

### STEP 7: Click "Approve Schedule Update"
- Click **Approve Schedule Update**.
- **What to say:**
  > *"AI recommends, evidence supports, but only the Human Planner validates and commits."*

### STEP 8: Show Schedule Mutation Feedback
- The green **Schedule Committed & Audited** banner immediately confirms:
  - `Activity: PIP-L6-0427`
  - `Actual Progress: 100% (was 0%)`
  - `Status: COMPLETED`
  - `Actual Finish: 08 Mar 2026`
  - `Updated By: Chief Planner`
- The system navigates to the **Schedule Master** tab showing `PIP-L6-0427` at **100% COMPLETED**.

### STEP 9: Show Governance Audit Trail
- Click **"Audit Trail"** tab.
- Point to the new immutable audit row:
  `Source (Time Agent) → Extraction (EVT) → AI Recommendation (PIP-L6-0427) → Planner Decision (APPROVE) → Schedule Update (0% -> 100%)`.

### STEP 10: Open Execution Memory
- Click **"Execution Memory"** tab.
- Show that approved execution history survives beyond live schedule updates:
  - Planned duration vs Actual duration in days.
  - Variance (-14 days).
  - Source document and Approved by provenance.
- In the search bar, type: **`piping erection V-105`** — instant dynamic search filtering!

### STEP 11: Demo Reset
- Click **"Reset Demo"** in the top navigation bar.
- Confirms reset to clean baseline in ~1 second.

### STEP 12: Run Case B — Medium / Ambiguous Scenario
- In Time Agent, click: **`MEDIUM: Suction line welding at PH-1`**
- Show what happens:
  - Multiple schedule candidates exist (`PIP-L6-1019` vs `PIP-L6-0502`).
  - Score margin is tight; system routes to **`MEDIUM CONFIDENCE — Planner Review Required`**.
  - **No schedule mutation occurs automatically.**
  - Click **"Inspect in Queue"** to show both candidate options with `[Select]` buttons for planner override.

### STEP 13: Demo Reset
- Click **"Reset Demo"** in top bar.

### STEP 14: Run Case C — No Match / Isolated Event
- In Time Agent, click: **`NO MATCH: Platform near T-204`**
- Input: `Temporary access platform installed beside Tank T-204.`
- Show what happens:
  - No matching L5/L6 activity exists in the baseline.
  - System tags it **`NO RELIABLE SCHEDULE MATCH`** and safely isolates it.
  - Clarification prompt is provided without corrupting the project schedule.

---

## Key Talking Points for Judges
1. **Deterministic & Offline:** Runs 100% locally with zero internet or API dependence during presentations.
2. **Explainable AI:** Uses multi-signal scoring (semantic + discipline + equipment + location + temporal) with explicit "Why This Match?" checkmarks instead of a black box.
3. **Institutional Memory:** Approved progress updates feed a historical database to prevent schedule optimism in future capital projects.

