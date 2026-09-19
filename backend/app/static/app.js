/**
 * InfraNexus AI - Enterprise Planner Workstation Frontend Logic
 * SIH26122 - Oil India Limited
 */

// State
const state = {
  activeTab: 'overview',
  summary: null,
  reviewQueue: [],
  activities: [],
  auditLogs: [],
  activeMatchDetail: null,
  currentUploadedDocId: null,
  systemHealth: null,
  historicalInsights: null,
  historySortCol: 'variance_days',
  historySortAsc: false
};

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', () => {
  initNav();
  loadAllData();
  setupIngestionEvents();
});

// Navigation Handling
function initNav() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const tabId = tab.dataset.tab;
      switchTab(tabId);
    });
  });
}

function switchTab(tabId) {
  state.activeTab = tabId;
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-view').forEach(v => {
    v.classList.toggle('active', v.id === `tab-${tabId}`);
  });

  if (tabId === 'overview') loadDashboardSummary();
  if (tabId === 'timeagent') focusTimeAgent();
  if (tabId === 'review') loadReviewQueue();
  if (tabId === 'activities') loadActivities();
  if (tabId === 'history') loadHistoricalInsights();
  if (tabId === 'audit') loadAuditTrail();
  if (tabId === 'system') loadSystemHealth();
}

// Initial Data Loading
async function loadAllData() {
  await Promise.all([
    loadDashboardSummary(),
    loadReviewQueue(),
    loadSystemHealth(),
    loadHistoricalInsights()
  ]);
}

// 1. Dashboard Summary
async function loadDashboardSummary() {
  try {
    const res = await fetch('/api/dashboard/summary');
    if (!res.ok) throw new Error('Failed to load dashboard summary');
    const data = await res.json();
    state.summary = data;
    renderDashboardSummary(data);
  } catch (err) {
    showToast('Error loading summary: ' + err.message, 'error');
  }
}

function renderDashboardSummary(data) {
  document.getElementById('metric-planned').innerText = `${data.planned_progress}%`;
  document.getElementById('metric-actual').innerText = `${data.actual_progress}%`;
  
  const varEl = document.getElementById('metric-variance');
  const variance = data.schedule_variance;
  varEl.innerText = `${variance >= 0 ? '+' : ''}${variance}%`;
  varEl.className = `metric-val ${variance >= 0 ? 'variance-positive' : 'variance-negative'}`;

  document.getElementById('metric-pending').innerText = data.pending_reviews;
  document.getElementById('metric-high-matches').innerText = data.high_confidence_matches;
  document.getElementById('metric-unmatched').innerText = data.unmatched_count;

  // Render S-Curve SVG Chart
  renderSCurveChart(data.planned_vs_actual_curve);

  // Render Status Activity breakdown
  renderStatusBreakdown(data);

  // Render recent audits
  renderRecentAudits(data.recent_approved_updates);
}

function renderSCurveChart(points) {
  const container = document.getElementById('scurve-chart');
  if (!points || !points.length) return;

  const width = 650;
  const height = 220;
  const padding = 35;

  const maxVal = 100;
  const xStep = (width - padding * 2) / (points.length - 1);

  // Planned Line points
  let plannedPoints = points.map((p, i) => {
    const x = padding + i * xStep;
    const y = height - padding - (p.planned / maxVal) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  // Actual Line points
  const actualItems = points.filter(p => p.actual !== null);
  let actualPoints = actualItems.map((p, i) => {
    const x = padding + i * xStep;
    const y = height - padding - (p.actual / maxVal) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  let svgHtml = `
    <svg viewBox="0 0 ${width} ${height}" style="width:100%; height:100%;">
      <!-- Grid lines -->
      <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="#cbd5e1" stroke-width="1"/>
      <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" stroke="#cbd5e1" stroke-width="1"/>
      
      <!-- Axis Labels -->
      <text x="${padding - 8}" y="${height - padding + 4}" font-size="10" fill="#64748b" text-anchor="end">0%</text>
      <text x="${padding - 8}" y="${(height - padding + padding)/2}" font-size="10" fill="#64748b" text-anchor="end">50%</text>
      <text x="${padding - 8}" y="${padding + 4}" font-size="10" fill="#64748b" text-anchor="end">100%</text>

      <!-- Planned Path (Blue dashed) -->
      <polyline fill="none" stroke="#0284c7" stroke-width="2.5" stroke-dasharray="4 3" points="${plannedPoints}"/>
      
      <!-- Actual Path (Teal solid) -->
      <polyline fill="none" stroke="#0d9488" stroke-width="3" points="${actualPoints}"/>
  `;

  // Plot actual points
  actualItems.forEach((p, i) => {
    const x = padding + i * xStep;
    const y = height - padding - (p.actual / maxVal) * (height - padding * 2);
    svgHtml += `<circle cx="${x}" cy="${y}" r="4" fill="#0d9488" stroke="#ffffff" stroke-width="1.5" />`;
  });

  // Milestone Labels
  points.forEach((p, i) => {
    const x = padding + i * xStep;
    svgHtml += `<text x="${x}" y="${height - 12}" font-size="9" fill="#64748b" text-anchor="middle">${p.milestone}</text>`;
  });

  svgHtml += `</svg>`;
  container.innerHTML = svgHtml;
}

function renderStatusBreakdown(data) {
  const total = data.total_activities || 1;
  const compPct = Math.round((data.completed_activities / total) * 100);
  const inProgPct = Math.round((data.in_progress_activities / total) * 100);
  const notStartPct = Math.round((data.not_started_activities / total) * 100);

  document.getElementById('breakdown-completed').innerText = `${data.completed_activities} (${compPct}%)`;
  document.getElementById('breakdown-in-progress').innerText = `${data.in_progress_activities} (${inProgPct}%)`;
  document.getElementById('breakdown-not-started').innerText = `${data.not_started_activities} (${notStartPct}%)`;

  document.getElementById('bar-completed').style.width = `${compPct}%`;
  document.getElementById('bar-in-progress').style.width = `${inProgPct}%`;
  document.getElementById('bar-not-started').style.width = `${notStartPct}%`;
}

function renderRecentAudits(audits) {
  const container = document.getElementById('recent-audits-list');
  if (!audits || !audits.length) {
    container.innerHTML = '<p class="text-muted" style="padding:1rem;">No recent updates committed.</p>';
    return;
  }

  container.innerHTML = audits.map(a => `
    <div style="display:flex; align-items:flex-start; justify-content:space-between; padding:0.75rem 0; border-bottom:1px solid #f1f5f9;">
      <div>
        <div style="display:flex; align-items:center; gap:0.5rem;">
          <span class="badge ${a.action === 'APPROVE' ? 'badge-high' : 'badge-medium'}">${a.action}</span>
          <span style="font-weight:600; font-size:0.85rem;">${a.final_activity_id || 'None'}</span>
        </div>
        <p style="font-size:0.75rem; color:#64748b; margin-top:0.25rem;">${a.notes || 'Committed update'}</p>
      </div>
      <div style="text-align:right;">
        <span style="font-size:0.75rem; font-weight:500; color:#0f172a;">${a.actor}</span>
        <div style="font-size:0.7rem; color:#94a3b8;">${new Date(a.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
      </div>
    </div>
  `).join('');
}

// 2. Review Queue Handling
async function loadReviewQueue(filterConf = null) {
  try {
    let url = '/api/review-queue';
    if (filterConf) url += `?confidence=${filterConf}`;
    const res = await fetch(url);
    const data = await res.json();
    state.reviewQueue = data;
    renderReviewQueue(data);
  } catch (err) {
    showToast('Failed to load review queue', 'error');
  }
}

function renderReviewQueue(items) {
  const container = document.getElementById('review-queue-body');
  document.getElementById('queue-count-badge').innerText = items.length;

  if (!items.length) {
    container.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:2rem; color:#64748b;">No pending review items found in queue.</td></tr>`;
    return;
  }

  container.innerHTML = items.map(item => {
    let confBadge = 'badge-low';
    if (item.confidence_tier === 'HIGH') confBadge = 'badge-high';
    else if (item.confidence_tier === 'MEDIUM') confBadge = 'badge-medium';
    else if (item.confidence_tier === 'UNMATCHED') confBadge = 'badge-unmatched';

    return `
      <tr>
        <td>
          <span class="badge ${confBadge}">${item.confidence_tier}</span>
          <div style="font-size:0.75rem; font-weight:700; color:#0284c7; margin-top:0.25rem;">Score: ${(item.final_score * 100).toFixed(1)}%</div>
        </td>
        <td>
          <div style="font-weight:600; font-size:0.825rem;">${escapeHtml(item.raw_text)}</div>
          <div style="font-size:0.725rem; color:#64748b; margin-top:0.2rem;">Doc: ${item.document_filename}</div>
        </td>
        <td>
          <div style="font-weight:600; font-size:0.825rem; color:#0f172a;">${item.activity_id || 'No Candidate'}</div>
          <div style="font-size:0.75rem; color:#475569;">${escapeHtml(item.activity_description)}</div>
        </td>
        <td><span class="badge-tag">${item.discipline}</span></td>
        <td>${item.location || '-'}</td>
        <td><span class="badge ${item.decision === 'APPROVED' ? 'badge-high' : 'badge-medium'}">${item.decision}</span></td>
        <td>
          <div style="display:flex; gap:0.4rem;">
            <button class="btn btn-outline btn-sm" onclick="openReviewModal('${item.event_id}')">Inspect</button>
            ${item.decision === 'PENDING' && item.confidence_tier !== 'UNMATCHED' ? `
              <button class="btn btn-success btn-sm" onclick="quickApprove('${item.match_id}')">Approve</button>
            ` : ''}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

// 3. Workstation Split-Screen Modal
async function openReviewModal(eventId) {
  try {
    const res = await fetch(`/api/matches/${eventId}`);
    if (!res.ok) throw new Error('Failed to load match detail');
    const data = await res.json();
    state.activeMatchDetail = data;
    renderReviewModal(data);
    document.getElementById('review-modal').classList.add('active');
  } catch (err) {
    showToast('Failed to open inspection: ' + err.message, 'error');
  }
}

function renderReviewModal(data) {
  const evt = data.event;
  const doc = data.source_document;
  const topCandidate = data.top_candidates && data.top_candidates[0];

  // Left Pane: Evidence & Document
  document.getElementById('modal-doc-name').innerText = doc ? doc.filename : 'Field DPR';
  document.getElementById('modal-evidence-text').innerText = evt.evidence_text || evt.raw_text;
  document.getElementById('modal-raw-doc-text').innerText = doc ? doc.raw_text : 'Source text unavailable.';

  // Right Pane: Extracted Fields
  document.getElementById('modal-extracted-grid').innerHTML = `
    <div><strong>Discipline:</strong> ${evt.discipline || 'Unknown'}</div>
    <div><strong>Location:</strong> ${evt.location || 'Not Specified'}</div>
    <div><strong>Equipment Tag:</strong> ${evt.equipment_id || 'None'}</div>
    <div><strong>Status:</strong> ${evt.status || 'In Progress'}</div>
    <div><strong>Quantity:</strong> ${evt.quantity ? `${evt.quantity} ${evt.unit || ''}` : 'N/A'}</div>
    <div><strong>Event Date:</strong> ${evt.event_date || 'Current'}</div>
  `;

  // Top candidate & scoring meters
  const candidatesContainer = document.getElementById('modal-candidates-list');
  if (!data.top_candidates || !data.top_candidates.length || data.confidence_tier === 'UNMATCHED') {
    candidatesContainer.innerHTML = `
      <div style="padding:1rem; background:#f8fafc; border:1px dashed #cbd5e1; border-radius:8px; text-align:center;">
        <span class="badge badge-unmatched" style="font-size:0.85rem;">UNMATCHED EVENT</span>
        <p style="font-size:0.8rem; color:#64748b; margin-top:0.5rem;">
          The system found no schedule activity matching this field report with acceptable confidence.
          No schedule update will be performed.
        </p>
      </div>
    `;
    document.getElementById('modal-actions-bar').innerHTML = `
      <button class="btn btn-outline" onclick="closeReviewModal()">Close</button>
      <button class="btn btn-danger" onclick="rejectActiveMatch('No matching activity')">Mark Ignored</button>
    `;
    return;
  }

  candidatesContainer.innerHTML = data.top_candidates.map((c, idx) => {
    const scores = c.scores;
    const isRecommended = idx === 0;
    return `
      <div style="border:1px solid ${isRecommended ? '#0284c7' : '#e2e8f0'}; border-radius:8px; padding:1rem; margin-bottom:0.75rem; background:${isRecommended ? '#f0f9ff' : '#ffffff'};">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <span class="badge ${isRecommended ? 'badge-high' : 'badge-medium'}">Rank #${c.rank}</span>
            <strong style="font-size:0.9rem; margin-left:0.4rem;">${c.activity_id}</strong>
            <div style="font-size:0.825rem; font-weight:600; color:#0f172a; margin-top:0.2rem;">${escapeHtml(c.description)}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:1.15rem; font-weight:800; color:#0284c7;">${(scores.final_score * 100).toFixed(1)}%</div>
            <span class="badge ${c.confidence_tier === 'HIGH' ? 'badge-high' : (c.confidence_tier === 'MEDIUM' ? 'badge-medium' : 'badge-low')}">${c.confidence_tier}</span>
          </div>
        </div>

        <!-- Scores Breakdown -->
        <div style="margin-top:0.75rem; background:#ffffff; padding:0.6rem; border-radius:6px; border:1px solid #e2e8f0;">
          <div class="score-row">
            <span class="score-name">Semantic Similarity (50%)</span>
            <div class="score-bar-bg"><div class="score-bar-fill" style="width:${scores.score_semantic * 100}%"></div></div>
            <span class="score-val">${scores.score_semantic.toFixed(2)}</span>
          </div>
          <div class="score-row">
            <span class="score-name">Discipline Match (15%)</span>
            <div class="score-bar-bg"><div class="score-bar-fill" style="width:${scores.score_discipline * 100}%"></div></div>
            <span class="score-val">${scores.score_discipline.toFixed(2)}</span>
          </div>
          <div class="score-row">
            <span class="score-name">Entity / Equipment (15%)</span>
            <div class="score-bar-bg"><div class="score-bar-fill" style="width:${scores.score_entity * 100}%"></div></div>
            <span class="score-val">${scores.score_entity.toFixed(2)}</span>
          </div>
          <div class="score-row">
            <span class="score-name">Location / Area (10%)</span>
            <div class="score-bar-bg"><div class="score-bar-fill" style="width:${scores.score_location * 100}%"></div></div>
            <span class="score-val">${scores.score_location.toFixed(2)}</span>
          </div>
          <div class="score-row">
            <span class="score-name">Schedule Temporal (10%)</span>
            <div class="score-bar-bg"><div class="score-bar-fill" style="width:${scores.score_temporal * 100}%"></div></div>
            <span class="score-val">${scores.score_temporal.toFixed(2)}</span>
          </div>
          ${scores.penalty_contradiction > 0 ? `
            <div class="score-row" style="color:#dc2626;">
              <span class="score-name">Contradiction Penalty</span>
              <div class="score-bar-bg"><div class="score-bar-fill" style="width:${scores.penalty_contradiction * 100}%; background:#dc2626;"></div></div>
              <span class="score-val">-${scores.penalty_contradiction.toFixed(2)}</span>
            </div>
          ` : ''}
        </div>

        <div style="font-size:0.75rem; color:#475569; margin-top:0.5rem;">
          <strong>Rationale:</strong> ${c.rationale}
        </div>
        ${c.contradictions ? `
          <div style="font-size:0.75rem; color:#dc2626; margin-top:0.25rem;">
            <strong>Warning:</strong> ${c.contradictions}
          </div>
        ` : ''}

        ${!isRecommended ? `
          <div style="margin-top:0.5rem; text-align:right;">
            <button class="btn btn-outline btn-sm" onclick="chooseCandidateForEdit('${c.activity_id}')">Select this activity</button>
          </div>
        ` : ''}
      </div>
    `;
  }).join('');

  // Action Buttons
  document.getElementById('modal-actions-bar').innerHTML = `
    <button class="btn btn-outline" onclick="closeReviewModal()">Cancel</button>
    <button class="btn btn-danger" onclick="rejectActiveMatch()">Reject Match</button>
    <button class="btn btn-outline" onclick="openEditModal()">Edit & Approve</button>
    <button class="btn btn-success" onclick="approveActiveMatch('${data.match_id}')">Approve Schedule Update</button>
  `;
}

function closeReviewModal() {
  document.getElementById('review-modal').classList.remove('active');
}

// 4. Ingestion & Preloaded Demo Scenarios
function setupIngestionEvents() {
  const fileInput = document.getElementById('file-upload-input');
  if (fileInput) {
    fileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (file) handleFileUpload(file);
    });
  }
}

async function handleFileUpload(file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('project_id', 'OIL-DNPE-2026');

  try {
    showToast(`Uploading ${file.name}...`, 'info');
    const res = await fetch('/api/documents', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error('Upload failed');
    const doc = await res.json();
    state.currentUploadedDocId = doc.id;
    showUploadedDocument(doc);
    showToast('File uploaded successfully! Ready for AI extraction.', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function showUploadedDocument(doc) {
  document.getElementById('ingest-preview-card').style.display = 'block';
  document.getElementById('ingest-doc-title').innerText = doc.filename;
  document.getElementById('ingest-doc-type').innerText = doc.file_type.toUpperCase();
  document.getElementById('ingest-raw-text').innerText = doc.raw_text || 'No text content';
}

async function runExtractionForCurrentDoc() {
  if (!state.currentUploadedDocId) {
    showToast('Please upload or select a document first', 'error');
    return;
  }

  try {
    showToast('Extracting structured events via InfraNexus AI pipeline...', 'info');
    const res = await fetch(`/api/extractions/${state.currentUploadedDocId}/run`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Extraction failed');
    const result = await res.json();
    showToast(`Extracted ${result.extracted_events_count} event(s) using ${result.provider}!`, 'success');
    
    // Refresh queue & dashboard
    await loadAllData();
    switchTab('review');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Pre-loaded Scenario Helper Functions
function loadDemoScenario(type) {
  let filename = '';
  let text = '';

  if (type === 'hero') {
    filename = 'DPR-OIL-2026-0308-01.txt';
    text = `OIL INDIA LIMITED - DAILY PROGRESS REPORT (DPR)
Project: Duliajan-Numaligarh Pipeline Expansion (DNPE)
Date: 2026-03-08
Report Ref: DPR-OIL-2026-0308-01
Site Engineer: D. Borah
Area: Pumping Station Upgrades / Vessel Yard

FIELD ACTIVITY LOG:
1. Spool erection near V-105 completed today. 14 spools installed.
2. Hydrotesting pre-checks initiated on drain manifolds.`;
  } else if (type === 'ambiguous') {
    filename = 'DPR-OIL-2026-0218-02.txt';
    text = `OIL INDIA LIMITED - DAILY PROGRESS REPORT (DPR)
Project: Duliajan-Numaligarh Pipeline Expansion (DNPE)
Date: 2026-02-18
Report Ref: DPR-OIL-2026-0218-02
Site Engineer: R. Gogoi
Area: Pump House PH-1

FIELD ACTIVITY LOG:
1. Suction line welding in progress at Pump House PH-1. Completed fit-up and weld for 4 joints today.`;
  } else if (type === 'unmatched') {
    filename = 'DPR-OIL-2026-0302-03.txt';
    text = `OIL INDIA LIMITED - DAILY PROGRESS REPORT (DPR)
Project: Duliajan-Numaligarh Pipeline Expansion (DNPE)
Date: 2026-03-02
Site Security & Admin: K. Sharma
Area: Main Gate & Camp Perimeter

DAILY LOG:
1. Catering supply van arrived at main gate 3 with provisions for the worker mess.`;
  }

  // Create virtual file and upload
  const blob = new Blob([text], { type: 'text/plain' });
  const file = new File([blob], filename);
  handleFileUpload(file);
}

// 5. Governance Actions: Approve, Edit, Reject
async function approveActiveMatch(matchId) {
  try {
    showToast('Committing approved update to project schedule...', 'info');
    const res = await fetch(`/api/matches/${matchId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decided_by: 'Chief Planner', notes: 'Approved via Planner Workstation' })
    });
    if (!res.ok) throw new Error('Approval transaction failed');
    const data = await res.json();
    showToast(data.message, 'success');
    closeReviewModal();
    await loadAllData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function quickApprove(matchId) {
  approveActiveMatch(matchId);
}

async function rejectActiveMatch(reason = 'Rejected by planner') {
  if (!state.activeMatchDetail) return;
  const matchId = state.activeMatchDetail.match_id;
  try {
    const res = await fetch(`/api/matches/${matchId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decided_by: 'Chief Planner', reason })
    });
    if (!res.ok) throw new Error('Rejection failed');
    showToast('Recommendation rejected. Schedule unchanged.', 'info');
    closeReviewModal();
    await loadAllData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openEditModal() {
  if (!state.activeMatchDetail) return;
  const cands = state.activeMatchDetail.top_candidates || [];
  const selectEl = document.getElementById('edit-override-activity');
  selectEl.innerHTML = cands.map(c => `
    <option value="${c.activity_id}">${c.activity_id} - ${c.description} (Rank #${c.rank})</option>
  `).join('');

  document.getElementById('edit-override-progress').value = state.activeMatchDetail.event.progress_percent || 100;
  document.getElementById('edit-modal').classList.add('active');
}

function closeEditModal() {
  document.getElementById('edit-modal').classList.remove('active');
}

function chooseCandidateForEdit(activityId) {
  openEditModal();
  document.getElementById('edit-override-activity').value = activityId;
}

async function submitEditAndApprove() {
  const matchId = state.activeMatchDetail.match_id;
  const actId = document.getElementById('edit-override-activity').value;
  const progress = parseFloat(document.getElementById('edit-override-progress').value);
  const notes = document.getElementById('edit-override-notes').value;

  try {
    const res = await fetch(`/api/matches/${matchId}/edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        override_activity_id: actId,
        new_progress_percent: progress,
        decided_by: 'Chief Planner',
        notes: notes || 'Planner manual candidate override'
      })
    });
    if (!res.ok) throw new Error('Edit transaction failed');
    const data = await res.json();
    showToast(data.message, 'success');
    closeEditModal();
    closeReviewModal();
    await loadAllData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// 6. Schedule & Activities Explorer
async function loadActivities(filterDiscipline = null) {
  try {
    let url = '/api/activities';
    if (filterDiscipline) url += `?discipline=${filterDiscipline}`;
    const res = await fetch(url);
    const data = await res.json();
    state.activities = data;
    renderActivitiesTable(data);
  } catch (err) {
    showToast('Failed to load activities', 'error');
  }
}

function renderActivitiesTable(activities) {
  const container = document.getElementById('activities-table-body');
  if (!activities.length) {
    container.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:2rem;">No activities found.</td></tr>`;
    return;
  }

  container.innerHTML = activities.map(a => {
    let statusClass = 'badge-not-started';
    if (a.status === 'COMPLETED' || a.actual_progress >= 100) statusClass = 'badge-completed';
    else if (a.status === 'IN_PROGRESS' || a.actual_progress > 0) statusClass = 'badge-in-progress';

    return `
      <tr>
        <td style="font-weight:700; color:#0284c7;">${a.activity_id}</td>
        <td>${escapeHtml(a.description)}</td>
        <td><span class="badge-tag">${a.discipline}</span></td>
        <td>${a.location || '-'}</td>
        <td style="font-size:0.75rem;">${a.planned_start || '-'} &rarr; ${a.planned_finish || '-'}</td>
        <td style="width:130px;">
          <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-bottom:0.2rem;">
            <span>${a.actual_progress}%</span>
            <span style="color:#64748b;">Plan: ${a.planned_progress}%</span>
          </div>
          <div class="progress-bar-wrap">
            <div class="progress-bar-fill" style="width:${a.actual_progress}%"></div>
          </div>
        </td>
        <td><span class="badge ${statusClass}">${a.status}</span></td>
      </tr>
    `;
  }).join('');
}

// 7. Audit Trail View
async function loadAuditTrail() {
  try {
    const res = await fetch('/api/audit');
    const data = await res.json();
    state.auditLogs = data;
    renderAuditTrail(data);
  } catch (err) {
    showToast('Failed to load audit trail', 'error');
  }
}

function renderAuditTrail(logs) {
  const container = document.getElementById('audit-trail-body');
  if (!logs.length) {
    container.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:2rem;">No audit logs recorded.</td></tr>`;
    return;
  }

  container.innerHTML = logs.map(l => `
    <tr>
      <td style="font-size:0.75rem; color:#64748b;">${new Date(l.timestamp).toLocaleString()}</td>
      <td><span class="badge ${l.action === 'APPROVE' ? 'badge-high' : (l.action === 'EDIT_APPROVE' ? 'badge-medium' : 'badge-low')}">${l.action}</span></td>
      <td style="font-weight:600;">${l.final_activity_id || 'None'}</td>
      <td style="font-size:0.8rem; color:#475569;">
        AI Pick: <strong>${l.ai_top_activity_id || 'None'}</strong>
        ${l.ai_score ? `<span style="color:#0284c7;">(${(l.ai_score * 100).toFixed(1)}%)</span>` : ''}
      </td>
      <td>
        ${l.previous_state ? `<span style="color:#64748b; font-size:0.75rem;">${l.previous_state.actual_progress || 0}% &rarr; ${l.resulting_state.actual_progress}%</span>` : '-'}
      </td>
      <td style="font-weight:500;">${l.actor}</td>
      <td style="font-size:0.8rem; color:#334155;">${escapeHtml(l.notes || '')}</td>
    </tr>
  `).join('');
}

// 8. System Health & Demo Reset
async function loadSystemHealth() {
  try {
    const res = await fetch('/api/health/system');
    const data = await res.json();
    state.systemHealth = data;
    
    document.getElementById('health-backend').innerText = data.backend.toUpperCase();
    document.getElementById('health-database').innerText = data.database.toUpperCase();
    document.getElementById('health-ai-provider').innerText = data.ai_provider;
    document.getElementById('health-embedding-provider').innerText = data.embedding_provider;
  } catch (err) {
    // Health check quiet fail
  }
}

async function triggerDemoReset() {
  if (!confirm('Reset entire InfraNexus AI database to clean baseline demo state?')) return;
  try {
    showToast('Resetting demo environment...', 'info');
    const res = await fetch('/api/demo/reset', { method: 'POST' });
    if (!res.ok) throw new Error('Reset failed');
    showToast('Demo environment reset successfully to clean initial state!', 'success');
    await loadAllData();
    switchTab('overview');
  } catch (err) {
    showToast('Reset failed: ' + err.message, 'error');
  }
}

// 4.5. Time Agent (Conversational Logging)
function focusTimeAgent() {
  setTimeout(() => {
    const input = document.getElementById('time-agent-input');
    if (input) input.focus();
  }, 50);
}

function clearTimeAgentChat() {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;
  container.innerHTML = `
    <div class="chat-msg chat-system" style="align-self: flex-start; max-width: 82%; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px 12px 12px 2px; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
      <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
        <span style="font-size:1.1rem;">🤖</span>
        <strong style="font-size:0.825rem; color:#0f172a;">Time Agent (InfraNexus AI)</strong>
        <span style="font-size:0.7rem; color:#94a3b8;">System Ready</span>
      </div>
      <p style="font-size:0.85rem; color:#334155; margin:0; line-height:1.45;">
        Chat cleared. Log today's field progress directly in natural text. I will extract structured engineering attributes, match against the baseline schedule, and route to the Planner Review Queue.
      </p>
    </div>
  `;
}

function sendQuickReply(text) {
  const input = document.getElementById('time-agent-input');
  if (input) {
    input.value = text;
    sendTimeAgentMessage();
  }
}

async function sendTimeAgentMessage() {
  const input = document.getElementById('time-agent-input');
  const sendBtn = document.getElementById('time-agent-send-btn');
  const container = document.getElementById('chat-messages-container');
  if (!input || !container) return;
  const text = input.value.trim();
  if (!text) return;

  // Render Supervisor user message bubble (right-aligned)
  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const userMsgEl = document.createElement('div');
  userMsgEl.className = 'chat-msg chat-user';
  userMsgEl.style.cssText = 'align-self: flex-end; max-width: 80%; background: #0284c7; color: #ffffff; border-radius: 12px 12px 2px 12px; padding: 0.85rem 1rem; box-shadow: 0 1px 3px rgba(2, 132, 199, 0.2);';
  userMsgEl.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem; gap:1rem;">
      <strong style="font-size:0.75rem; color:#e0f2fe;">👷 Site Supervisor</strong>
      <span style="font-size:0.65rem; color:#bae6fd;">${timeStr}</span>
    </div>
    <div style="font-size:0.875rem; line-height:1.4;">${escapeHtml(text)}</div>
  `;
  container.appendChild(userMsgEl);
  input.value = '';
  container.scrollTop = container.scrollHeight;

  // Show temporary "Thinking..." bubble
  const typingEl = document.createElement('div');
  typingEl.className = 'chat-msg chat-typing';
  typingEl.style.cssText = 'align-self: flex-start; max-width: 75%; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px 12px 12px 2px; padding: 0.75rem 1rem; color: #64748b; font-size: 0.8rem;';
  typingEl.innerHTML = `<span>⚙️ Analyzing text & matching against Primavera P6 baseline...</span>`;
  container.appendChild(typingEl);
  container.scrollTop = container.scrollHeight;

  if (sendBtn) sendBtn.disabled = true;

  try {
    const res = await fetch('/api/v1/events/quick-log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        project_id: 'OIL-DNPE-2026',
        submitted_by: 'Site Supervisor (Field)'
      })
    });

    typingEl.remove();

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to process quick log');
    }

    const data = await res.json();
    const botMsgEl = document.createElement('div');
    botMsgEl.className = 'chat-msg chat-system';
    botMsgEl.style.cssText = 'align-self: flex-start; max-width: 85%; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px 12px 12px 2px; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);';

    let badgeClass = 'badge-low';
    if (data.confidence_tier === 'HIGH') badgeClass = 'badge-high';
    else if (data.confidence_tier === 'MEDIUM') badgeClass = 'badge-medium';
    else if (data.confidence_tier === 'UNMATCHED') badgeClass = 'badge-unmatched';

    const fields = data.extracted_fields || {};
    const hasMatch = data.matched_activity_id && data.confidence_tier !== 'UNMATCHED';
    const confMsg = data.message || data.confirmation_message || 'Event processed.';
    const scoreVal = data.top_score !== undefined ? data.top_score : (data.score !== undefined ? data.score : 0);
    const scorePct = (scoreVal * 100).toFixed(1);

    botMsgEl.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
        <div style="display:flex; align-items:center; gap:0.4rem;">
          <span style="font-size:1.1rem;">🤖</span>
          <strong style="font-size:0.825rem; color:#0f172a;">Time Agent</strong>
        </div>
        <div style="display:flex; align-items:center; gap:0.4rem;">
          <span class="badge ${badgeClass}">${data.confidence_tier} (${scorePct}%)</span>
        </div>
      </div>
      <div style="font-size:0.875rem; color:#1e293b; margin-bottom:0.75rem; line-height:1.45; background:#f8fafc; padding:0.6rem 0.75rem; border-radius:6px; border-left:3px solid ${data.confidence_tier === 'HIGH' ? 'var(--success)' : (data.confidence_tier === 'MEDIUM' ? 'var(--warning)' : 'var(--danger)')};">
        ${escapeHtml(confMsg)}
      </div>

      <!-- Extracted Fields Table/Grid -->
      <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:6px; padding:0.6rem 0.75rem; margin-bottom:0.75rem; font-size:0.775rem;">
        <div style="font-weight:700; color:#475569; margin-bottom:0.35rem; text-transform:uppercase; letter-spacing:0.03em;">Extracted Field Event</div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:0.35rem; color:#334155;">
          <div><span style="color:#64748b;">Discipline:</span> <strong>${escapeHtml(fields.discipline || 'Unknown')}</strong></div>
          <div><span style="color:#64748b;">Location:</span> <strong>${escapeHtml(fields.location || 'General Site')}</strong></div>
          <div><span style="color:#64748b;">Status:</span> <strong>${escapeHtml(fields.status || 'In Progress')}</strong></div>
          <div><span style="color:#64748b;">Activity:</span> <strong>${escapeHtml(fields.activity_description || text)}</strong></div>
        </div>
      </div>

      ${hasMatch ? `
        <div style="display:flex; justify-content:space-between; align-items:center; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:6px; padding:0.6rem 0.75rem;">
          <div>
            <div style="font-size:0.7rem; color:#166534; font-weight:700; text-transform:uppercase;">Matched P6 Activity</div>
            <div style="font-size:0.825rem; font-weight:700; color:#14532d;">${escapeHtml(data.matched_activity_id)}: ${escapeHtml(data.matched_activity_description || '')}</div>
          </div>
          <button class="btn btn-outline btn-sm" onclick="switchTab('review'); openReviewModal('${data.event_id}')" style="background:#ffffff; border-color:#86efac; color:#166534; white-space:nowrap; margin-left:0.75rem;">
            Inspect in Queue &rarr;
          </button>
        </div>
      ` : `
        <div style="display:flex; justify-content:space-between; align-items:center; background:#fef2f2; border:1px solid #fecaca; border-radius:6px; padding:0.6rem 0.75rem;">
          <div>
            <div style="font-size:0.7rem; color:#991b1b; font-weight:700; text-transform:uppercase;">Clarification Prompt</div>
            <div style="font-size:0.8rem; color:#7f1d1d;">No confident activity match. Please provide line number, equipment ID, or area.</div>
          </div>
          <button class="btn btn-outline btn-sm" onclick="switchTab('review')" style="background:#ffffff; border-color:#fca5a5; color:#991b1b; white-space:nowrap; margin-left:0.75rem;">
            View Review Queue &rarr;
          </button>
        </div>
      `}
    `;

    container.appendChild(botMsgEl);
    container.scrollTop = container.scrollHeight;

    // Refresh review queue badge and queue data
    loadReviewQueue();
    loadDashboardSummary();
    showToast('Event logged & routed to Planner Review Queue!', 'success');
  } catch (err) {
    if (typingEl.parentNode) typingEl.remove();
    const errEl = document.createElement('div');
    errEl.className = 'chat-msg chat-system';
    errEl.style.cssText = 'align-self: flex-start; max-width: 80%; background: #fee2e2; border: 1px solid #fca5a5; border-radius: 12px 12px 12px 2px; padding: 0.85rem 1rem; color: #991b1b; font-size: 0.825rem;';
    errEl.innerHTML = `<strong>Error logging event:</strong> ${escapeHtml(err.message)}`;
    container.appendChild(errEl);
    container.scrollTop = container.scrollHeight;
    showToast('Quick log failed: ' + err.message, 'error');
  } finally {
    if (sendBtn) sendBtn.disabled = false;
  }
}

// 7.5. Institutional Memory Analytics
async function loadHistoricalInsights(discipline) {
  if (discipline === undefined) {
    const filterEl = document.getElementById('history-discipline-filter');
    discipline = filterEl ? filterEl.value : '';
  }
  
  try {
    let url = '/api/v1/insights/history';
    if (discipline) {
      url += `?discipline=${encodeURIComponent(discipline)}`;
    }
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load historical insights');
    const data = await res.json();
    state.historicalInsights = data;
    renderHistoricalInsights(data);
  } catch (err) {
    showToast('Error loading institutional memory: ' + err.message, 'error');
  }
}

function filterHistoryByDiscipline(discipline) {
  loadHistoricalInsights(discipline);
}

function renderHistoricalInsights(data) {
  if (!data) return;
  
  // Summary Metrics
  const compEl = document.getElementById('hist-metric-completed');
  const overEl = document.getElementById('hist-metric-overruns');
  const ontimeEl = document.getElementById('hist-metric-ontime');
  const avgVarEl = document.getElementById('hist-metric-avg-var');
  const countEl = document.getElementById('history-record-count');

  if (compEl) compEl.innerText = data.total_completed_activities;
  if (overEl) overEl.innerText = data.total_overrun_count;
  if (ontimeEl) ontimeEl.innerText = data.total_ontime_or_early_count;
  
  if (avgVarEl) {
    const avg = data.project_avg_variance_days;
    avgVarEl.innerText = `${avg > 0 ? '+' : ''}${avg} d`;
    avgVarEl.style.color = avg > 0 ? 'var(--danger)' : 'var(--success)';
  }

  if (countEl) {
    countEl.innerText = `Showing ${data.activities.length} completed activities${data.discipline_filter ? ` for ${data.discipline_filter}` : ''}`;
  }

  // Discipline Overrun Breakdown Cards
  const breakdownContainer = document.getElementById('history-discipline-breakdown');
  if (breakdownContainer && data.discipline_summary) {
    if (!data.discipline_summary.length) {
      breakdownContainer.innerHTML = `<div style="grid-column:1/-1; color:#64748b; font-size:0.85rem; padding:1rem; text-align:center;">No discipline summaries available for current selection.</div>`;
    } else {
      breakdownContainer.innerHTML = data.discipline_summary.map(ds => {
        const hasOverruns = ds.total_overrun_days > 0;
        return `
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:1rem; display:flex; flex-direction:column; justify-content:space-between;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.5rem;">
              <strong style="font-size:0.9rem; color:#0f172a;">${escapeHtml(ds.discipline)}</strong>
              <span class="badge ${hasOverruns ? 'badge-low' : 'badge-high'}">
                ${ds.avg_variance_days > 0 ? '+' : ''}${ds.avg_variance_days} d avg
              </span>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; font-size:0.775rem; margin-top:0.5rem; color:#475569;">
              <div>Total Overrun: <strong style="color:${hasOverruns ? 'var(--danger)' : 'var(--success)'};">${ds.total_overrun_days} d</strong></div>
              <div>Overrun Items: <strong style="color:var(--danger);">${ds.overrun_count}</strong></div>
              <div>On-Time / Early: <strong style="color:var(--success);">${ds.ontime_count}</strong></div>
              <div>Total Completed: <strong>${ds.activity_count}</strong></div>
            </div>
          </div>
        `;
      }).join('');
    }
  }

  // Render Table
  renderHistoryTable(data.activities);
}

function renderHistoryTable(activities) {
  const tbody = document.getElementById('history-table-body');
  if (!tbody) return;

  if (!activities || !activities.length) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:2rem; color:#64748b;">No completed historical activities found.</td></tr>`;
    return;
  }

  // Sort activities based on state.historySortCol & state.historySortAsc
  const sorted = [...activities].sort((a, b) => {
    let valA = a[state.historySortCol];
    let valB = b[state.historySortCol];
    if (typeof valA === 'string') {
      valA = valA.toLowerCase();
      valB = (valB || '').toLowerCase();
      return state.historySortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    }
    return state.historySortAsc ? (valA - valB) : (valB - valA);
  });

  tbody.innerHTML = sorted.map(act => {
    const isOverrun = act.variance_days > 0;
    const isAhead = act.variance_days < 0;
    const varColor = isOverrun ? 'var(--danger)' : 'var(--success)';
    const varSign = act.variance_days > 0 ? '+' : '';
    
    let statusBadge = '<span class="badge badge-high">ON TIME</span>';
    if (isOverrun) {
      statusBadge = '<span class="badge badge-low">OVERRUN</span>';
    } else if (isAhead) {
      statusBadge = '<span class="badge badge-high">AHEAD</span>';
    }

    return `
      <tr>
        <td style="font-weight:700; color:#0284c7; white-space:nowrap;">${escapeHtml(act.activity_id)}</td>
        <td style="font-weight:500; max-width:320px;">${escapeHtml(act.description)}</td>
        <td><span class="badge-tag">${escapeHtml(act.discipline)}</span></td>
        <td style="font-size:0.775rem; color:#64748b; white-space:nowrap;">${act.planned_start} &rarr; ${act.planned_finish}</td>
        <td style="font-size:0.775rem; color:#475569; white-space:nowrap;">${act.actual_start} &rarr; ${act.actual_finish}</td>
        <td style="text-align:center; font-weight:600;">${act.planned_duration_days} d</td>
        <td style="text-align:center; font-weight:600;">${act.actual_duration_days} d</td>
        <td style="text-align:center; font-weight:700; color:${varColor};">
          ${varSign}${act.variance_days} d
        </td>
        <td style="text-align:center;">${statusBadge}</td>
      </tr>
    `;
  }).join('');
}

function sortHistoryTable(col) {
  if (state.historySortCol === col) {
    state.historySortAsc = !state.historySortAsc;
  } else {
    state.historySortCol = col;
    state.historySortAsc = false; // Default desc for numbers/dates
  }
  if (state.historicalInsights && state.historicalInsights.activities) {
    renderHistoryTable(state.historicalInsights.activities);
  }
}

// Toast Helpers
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast';
  
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '⚠️';

  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
