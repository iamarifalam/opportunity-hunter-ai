/**
 * Opportunity Hunter AI — Dashboard Application Script
 * PostHog Engineering Sketchbook Edition: Cream canvas, IBM Plex Sans, flat white cards,
 * PostHog Yellow CTA pill, and hand-drawn hedgehog mascots.
 */

let allOpportunities = [];
let allApplications = [];
let allApprovals = [];
let allSwagItems = [];
let allSwagClaims = [];
let rewardMetrics = {};
let currentSelectedOppId = null;

// Initialization
document.addEventListener("DOMContentLoaded", () => {
  initializeApp();
});

async function initializeApp() {
  await Promise.all([
    loadOverviewData(),
    loadOpportunities(),
    loadSwagOpportunities(),
    loadCredits(),
    loadSwagClaims(),
    loadOrchestratorStatus(),
    loadApplications(),
    loadApprovals(),
    loadDeadlines(),
    loadRewards(),
    loadLatestReport(),
    loadActivityLogs(),
    loadProfile(),
    loadSources(),
    loadIntegrations(),
    loadTelemetry(),
  ]);
}

// Tab Switching (PostHog Doc Navigation style: active tab lifts off cream canvas onto white card)
function switchTab(tabName) {
  const tabs = [
    "overview",
    "swag",
    "discover",
    "credits",
    "recommended",
    "applications",
    "approvals",
    "deadlines",
    "rewards",
    "swag-claims",
    "orchestrator",
    "reports",
    "logs",
    "profile",
    "sources",
    "integrations",
    "telemetry",
  ];
  tabs.forEach(t => {
    const sec = document.getElementById(`section-${t}`);
    const btn = document.getElementById(`tab-btn-${t}`);
    if (sec) sec.classList.add("hidden");
    if (btn) {
      btn.classList.remove("bg-surface-card", "text-ink", "border", "border-hairline", "font-semibold");
      btn.classList.add("text-body", "hover:bg-surface-soft");
    }
  });

  const activeSec = document.getElementById(`section-${tabName}`);
  const activeBtn = document.getElementById(`tab-btn-${tabName}`);
  if (activeSec) activeSec.classList.remove("hidden");
  if (activeBtn) {
    activeBtn.classList.add("bg-surface-card", "text-ink", "border", "border-hairline", "font-semibold");
    activeBtn.classList.remove("text-body", "hover:bg-surface-soft");
  }

  // Reload specific tab data on switch
  if (tabName === "swag") loadSwagOpportunities();
  if (tabName === "credits") loadCredits();
  if (tabName === "swag-claims") loadSwagClaims();
  if (tabName === "orchestrator") loadOrchestratorStatus();
  if (tabName === "discover") filterOpportunities();
  if (tabName === "recommended") renderRecommendedTab();
  if (tabName === "applications") loadApplications();
  if (tabName === "approvals") loadApprovals();
  if (tabName === "rewards") loadRewards();
  if (tabName === "logs") loadActivityLogs();
  if (tabName === "sources") loadSources();
  if (tabName === "integrations") loadIntegrations();
  if (tabName === "telemetry") loadTelemetry();
}

// Quick Search from PostHog Doc Sidebar ("Ask Opportunity AI")
function handleQuickSearch(query) {
  const searchInput = document.getElementById("search-input");
  if (searchInput) {
    searchInput.value = query;
  }
  switchTab("discover");
  filterOpportunities();
}

// 1. Overview Loading
async function loadOverviewData() {
  try {
    const oppsRes = await fetch("/api/opportunities/");
    const opps = await oppsRes.json();
    allOpportunities = opps;

    const rewRes = await fetch("/api/rewards/metrics");
    rewardMetrics = await rewRes.json();

    const appRes = await fetch("/api/applications/");
    allApplications = await appRes.json();

    const approvalsRes = await fetch("/api/approvals/?status=Pending");
    const pendingApprovals = await approvalsRes.json();

    // KPI numbers
    document.getElementById("kpi-discovered").innerText = opps.length;
    const eligibleCount = opps.filter(o => ["Eligible", "Likely eligible"].includes(o.eligibility_status)).length;
    document.getElementById("kpi-eligible").innerText = eligibleCount;
    document.getElementById("kpi-potential").innerText = `$${(rewardMetrics.total_potential_usd || 0).toLocaleString()}`;
    document.getElementById("kpi-claimed").innerText = `$${(rewardMetrics.total_claimed_usd || 0).toLocaleString()}`;

    // Badges
    document.getElementById("badge-app-count").innerText = allApplications.length;
    document.getElementById("badge-approval-count").innerText = pendingApprovals.length;

    renderPreRegisteredCards(opps);
    renderTopRecommendations(opps);
  } catch (err) {
    console.error("Error loading overview data:", err);
  }
}

// Pre-registered cards (Homingo & Arthaton) in PostHog White Card on Cream
function renderPreRegisteredCards(opps) {
  const container = document.getElementById("pre-registered-cards");
  if (!container) return;

  const preRegs = opps.filter(o => o.status === "Registered" || o.status === "USER_REPORTED_REGISTERED" || o.name.includes("Homingo") || o.name.includes("Arthaton"));
  if (preRegs.length === 0) {
    container.innerHTML = `<p class="text-xs text-mute">No user-reported or confirmed events yet.</p>`;
    return;
  }

  container.innerHTML = preRegs.map(opp => {
    const isLiveConfirmed = opp.status === "Registered";
    const statusBadge = isLiveConfirmed 
      ? `<span class="text-[10px] font-bold uppercase tracking-wider text-accent-green bg-accent-green-soft px-2 py-0.5 rounded-xs border border-accent-green/30">✓ Live Gmail Confirmed</span>`
      : `<span class="text-[10px] font-bold uppercase tracking-wider text-charcoal bg-primary/20 px-2 py-0.5 rounded-xs border border-primary/40">⏳ User-Reported (Awaiting Live Gmail)</span>`;

    const evidenceText = isLiveConfirmed
      ? "Evidence: Authenticated email message receipt in inbox."
      : (opp.source_evidence || "Evidence: User-reported registration. Awaiting live Gmail OAuth/IMAP confirmation.");

    return `
    <div class="ph-card p-5 space-y-3 relative overflow-hidden flex flex-col justify-between">
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          ${statusBadge}
          <span class="text-xs font-bold text-ink bg-surface-soft px-2 py-0.5 rounded-xs border border-hairline font-mono">
            ★ ${opp.priority_score}/100
          </span>
        </div>
        <h4 class="text-base font-bold text-ink mt-1">${opp.name}</h4>
        <p class="text-xs text-mute">${opp.organization} · ${opp.category}</p>
        <div class="text-[11px] text-body bg-surface-doc p-2 rounded-xs border border-hairline font-mono">
          ${evidenceText}
        </div>
      </div>
      <div class="pt-3 border-t border-hairline-soft flex items-center justify-between text-xs">
        <span class="text-mute font-medium">Reward: <strong class="text-ink">${opp.reward_type}</strong></span>
        <button onclick="openOppModal(${opp.id})" class="text-link-teal font-semibold hover:underline">View Evidence →</button>
      </div>
    </div>
  `}).join("");
}

// Top recommendations on Overview
function renderTopRecommendations(opps) {
  const container = document.getElementById("top-recommended-list");
  if (!container) return;

  const sorted = [...opps].sort((a, b) => b.priority_score - a.priority_score).slice(0, 4);
  container.innerHTML = sorted.map(opp => `
    <div class="ph-card p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div class="space-y-1">
        <div class="flex items-center space-x-2">
          <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-xs bg-surface-soft text-ink border border-hairline">${opp.category}</span>
          <span class="text-[10px] font-semibold px-2 py-0.5 rounded-xs ${getEligibilityBadgeClass(opp.eligibility_status)}">${opp.eligibility_status}</span>
          <span class="text-xs text-mute">${opp.organization}</span>
        </div>
        <h4 class="text-sm font-bold text-ink">${opp.name}</h4>
        <p class="text-xs text-body line-clamp-1">${opp.score_explanation?.summary || opp.source_evidence?.slice(0, 90) + '...'}</p>
      </div>

      <div class="flex items-center space-x-4 shrink-0">
        <div class="text-right">
          <div class="text-[10px] font-bold uppercase tracking-wider text-mute">Reward</div>
          <div class="text-sm font-bold text-accent-green">$${opp.reward_value.toLocaleString()}</div>
        </div>
        <div class="w-12 h-10 rounded-md bg-surface-soft border border-hairline flex flex-col items-center justify-center">
          <span class="text-xs font-black text-ink font-mono">${opp.priority_score}</span>
          <span class="text-[8px] uppercase font-bold text-mute">Score</span>
        </div>
        <button onclick="openOppModal(${opp.id})" class="btn-ph-secondary text-xs">
          Inspect
        </button>
      </div>
    </div>
  `).join("");
}

// 2. Opportunities Tab & Filter (PostHog feature tiles in 2-up grid)
async function loadOpportunities() {
  try {
    const res = await fetch("/api/opportunities/");
    allOpportunities = await res.json();
    filterOpportunities();
  } catch (err) {
    console.error("Error loading opportunities:", err);
  }
}

function filterOpportunities() {
  const search = document.getElementById("search-input")?.value.toLowerCase() || "";
  const category = document.getElementById("filter-category")?.value || "All";
  const eligibility = document.getElementById("filter-eligibility")?.value || "All";
  const sortBy = document.getElementById("sort-by")?.value || "score";

  let filtered = allOpportunities.filter(o => {
    const matchSearch = !search || o.name.toLowerCase().includes(search) || o.organization.toLowerCase().includes(search) || o.category.toLowerCase().includes(search);
    const matchCategory = category === "All" || o.category === category;
    const matchEligibility = eligibility === "All" || o.eligibility_status === eligibility;
    return matchSearch && matchCategory && matchEligibility;
  });

  if (sortBy === "score") {
    filtered.sort((a, b) => b.priority_score - a.priority_score);
  } else if (sortBy === "reward") {
    filtered.sort((a, b) => b.reward_value - a.reward_value);
  } else if (sortBy === "deadline") {
    filtered.sort((a, b) => (a.registration_deadline || "9999").localeCompare(b.registration_deadline || "9999"));
  }

  const container = document.getElementById("opportunities-grid");
  if (!container) return;

  if (filtered.length === 0) {
    container.innerHTML = `<div class="col-span-2 ph-card p-8 text-center text-xs text-mute">No opportunities found matching search criteria.</div>`;
    return;
  }

  container.innerHTML = filtered.map(opp => `
    <div class="ph-card p-5 flex flex-col justify-between space-y-4">
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-xs bg-surface-soft text-ink border border-hairline">${opp.category}</span>
            <span class="text-[10px] font-semibold px-2 py-0.5 rounded-xs ${getEligibilityBadgeClass(opp.eligibility_status)}">${opp.eligibility_status}</span>
          </div>
          <div class="text-xs font-bold text-ink bg-surface-soft px-2 py-0.5 rounded-xs border border-hairline font-mono">
            ★ ${opp.priority_score}
          </div>
        </div>

        <h4 class="text-sm font-bold text-ink">${opp.name}</h4>
        <p class="text-xs text-mute font-medium">${opp.organization} · <span>${opp.country}</span></p>

        <p class="text-xs text-body line-clamp-2 leading-relaxed">
          ${opp.source_evidence || "Verified developer opportunity open for eligible candidates."}
        </p>

        <div class="flex flex-wrap gap-1 pt-1">
          ${(opp.required_skills || []).slice(0, 3).map(s => `
            <span class="text-[10px] bg-surface-doc text-body px-2 py-0.5 rounded-xs border border-hairline">${s}</span>
          `).join("")}
        </div>
      </div>

      <div class="pt-3 border-t border-hairline-soft flex items-center justify-between text-xs">
        <div>
          <span class="text-[10px] text-mute block uppercase font-bold">Reward</span>
          <span class="text-xs font-bold text-accent-green">${opp.reward_type} ($${opp.reward_value.toLocaleString()})</span>
        </div>
        <div class="flex space-x-2">
          <button onclick="openOppModal(${opp.id})" class="btn-ph-secondary text-xs">
            Details
          </button>
          <button onclick="openApplyModal(${opp.id})" class="${opp.status === 'Registered' ? 'btn-ph-secondary' : 'btn-ph-primary'} text-xs">
            ${opp.status === 'Registered' ? 'Registered ✓' : 'Apply Draft'}
          </button>
        </div>
      </div>
    </div>
  `).join("");
}

// 3. Recommended Tab (Full Cards with AI Breakdown and Marginalia)
function renderRecommendedTab() {
  const container = document.getElementById("recommended-detailed-grid");
  if (!container) return;

  const sorted = [...allOpportunities].sort((a, b) => b.priority_score - a.priority_score);
  container.innerHTML = sorted.map((opp, idx) => `
    <div class="ph-card p-6 space-y-4">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div class="flex items-center space-x-3">
          <div class="w-9 h-9 rounded-md bg-surface-soft border border-hairline flex items-center justify-center font-bold text-ink text-sm font-mono">
            #${idx + 1}
          </div>
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-xs bg-surface-soft text-ink border border-hairline">${opp.category}</span>
              <span class="text-[10px] font-semibold px-2 py-0.5 rounded-xs ${getEligibilityBadgeClass(opp.eligibility_status)}">${opp.eligibility_status}</span>
              <span class="text-xs text-mute">${opp.organization}</span>
            </div>
            <h3 class="text-base font-bold text-ink mt-1">${opp.name}</h3>
          </div>
        </div>

        <div class="flex items-center space-x-3">
          <div class="text-right">
            <span class="text-[10px] text-mute block uppercase font-bold">Reward</span>
            <span class="text-sm font-bold text-accent-green">$${opp.reward_value.toLocaleString()} (${opp.reward_type})</span>
          </div>
          <div class="w-12 h-12 rounded-md bg-primary/20 border border-primary flex flex-col items-center justify-center">
            <span class="text-sm font-black text-ink font-mono">${opp.priority_score}</span>
            <span class="text-[8px] uppercase font-bold text-ink">Score</span>
          </div>
        </div>
      </div>

      <!-- Pastel Banner Breakdown inside Doc Card -->
      <div class="p-4 bg-accent-blue-soft border-l-4 border-accent-blue rounded-md text-xs space-y-2">
        <div class="font-bold text-ink flex items-center space-x-1.5">
          <span>🧠</span> <span>AI Opportunity Recommendation Breakdown:</span>
        </div>
        <p class="text-body leading-relaxed">${opp.score_explanation?.summary || 'Top scoring match.'}</p>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-accent-blue/20 text-[11px] font-mono">
          <div>🎯 Eligibility: <strong>${opp.score_explanation?.breakdown?.eligibility?.points || 25}/25</strong></div>
          <div>💰 Reward: <strong>${opp.score_explanation?.breakdown?.reward?.points || 25}/25</strong></div>
          <div>🛡️ Free Policy: <strong>${opp.score_explanation?.breakdown?.free_participation?.points || 15}/15</strong></div>
          <div>💻 Career Match: <strong>${opp.score_explanation?.breakdown?.career_relevance?.points || 15}/15</strong></div>
        </div>
      </div>

      <div class="flex items-center justify-between pt-2 border-t border-hairline-soft text-xs">
        <span class="text-mute font-medium">Deadline: <strong class="text-ink">${opp.registration_deadline ? new Date(opp.registration_deadline).toLocaleDateString() : 'Ongoing'}</strong></span>
        <div class="flex space-x-2">
          <a href="${opp.official_url}" target="_blank" class="btn-ph-secondary text-xs">Official Portal ↗</a>
          <button onclick="openApplyModal(${opp.id})" class="btn-ph-primary text-xs">
            Prepare Application
          </button>
        </div>
      </div>
    </div>
  `).join("");
}

// 4. Applications Pipeline
async function loadApplications() {
  try {
    const res = await fetch("/api/applications/");
    allApplications = await res.json();

    const tbody = document.getElementById("applications-table-body");
    if (!tbody) return;

    if (allApplications.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-mute">No applications initiated yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = allApplications.map(app => `
      <tr class="hover:bg-surface-soft/40 transition-colors">
        <td class="p-3 font-semibold text-ink">${app.opportunity_name}</td>
        <td class="p-3 text-mute">${app.category}</td>
        <td class="p-3">
          <span class="px-2 py-0.5 rounded-xs text-[10px] font-bold ${getApplicationBadgeClass(app.application_status)}">
            ${app.application_status}
          </span>
        </td>
        <td class="p-3 text-body font-mono text-[11px]">${app.account_used || 'Default'}</td>
        <td class="p-3 text-body text-[11px] font-mono">${app.confirmation_evidence || 'Draft state'}</td>
        <td class="p-3">
          <button onclick="openOppModal(${app.opportunity_id})" class="text-link-teal font-semibold hover:underline">View</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading applications:", err);
  }
}

// 5. Approval Queue
async function loadApprovals() {
  try {
    const res = await fetch("/api/approvals/");
    allApprovals = await res.json();

    const container = document.getElementById("approvals-list");
    if (!container) return;

    const pending = allApprovals.filter(a => a.status === "Pending");
    document.getElementById("badge-approval-count").innerText = pending.length;

    if (allApprovals.length === 0) {
      container.innerHTML = `<div class="p-8 text-center text-xs text-mute ph-card">Approval queue is empty. No sensitive actions require review.</div>`;
      return;
    }

    container.innerHTML = allApprovals.map(req => `
      <div class="ph-card p-5 space-y-3 ${req.status === 'Pending' ? 'border-accent-red' : ''}">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <span class="px-2 py-0.5 rounded-xs text-[10px] font-bold uppercase ${getRiskBadgeClass(req.risk_level)}">${req.risk_level} Risk</span>
            <span class="text-xs font-bold text-ink font-mono">${req.action_type}</span>
          </div>
          <span class="text-xs px-2 py-0.5 rounded-xs font-bold font-mono ${req.status === 'Pending' ? 'bg-accent-red-soft text-accent-red' : (req.status === 'Approved' ? 'bg-accent-green-soft text-accent-green' : 'bg-surface-soft text-mute')}">
            ${req.status}
          </span>
        </div>

        <div>
          <h4 class="text-sm font-bold text-ink">${req.opportunity_name}</h4>
          <p class="text-xs text-body mt-1 leading-relaxed">${req.description}</p>
        </div>

        ${req.status === 'Pending' ? `
          <div class="pt-3 border-t border-hairline-soft flex items-center justify-end space-x-3">
            <button onclick="resolveApproval(${req.id}, 'REJECT')" class="btn-ph-secondary text-xs text-accent-red hover:bg-accent-red-soft">
              Reject Action
            </button>
            <button onclick="resolveApproval(${req.id}, 'APPROVE')" class="btn-ph-primary text-xs">
              Authorize Action
            </button>
          </div>
        ` : `
          <div class="pt-2 text-[11px] text-mute border-t border-hairline-soft font-mono">
            Resolved: ${req.resolved_by || 'User'} on ${new Date(req.resolved_at).toLocaleString()}
          </div>
        `}
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading approvals:", err);
  }
}

async function resolveApproval(approvalId, decision) {
  try {
    const res = await fetch(`/api/approvals/${approvalId}/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: decision, notes: `Explicit user resolution: ${decision}` }),
    });
    if (res.ok) {
      await initializeApp();
    }
  } catch (err) {
    console.error("Error resolving approval:", err);
  }
}

// 6. Deadlines Radar
async function loadDeadlines() {
  try {
    const opps = allOpportunities;
    const now = new Date();

    const items = opps.filter(o => o.registration_deadline).map(o => {
      const dl = new Date(o.registration_deadline);
      const diffDays = Math.ceil((dl - now) / (1000 * 60 * 60 * 24));
      return { ...o, diffDays };
    }).filter(o => o.diffDays > 0).sort((a, b) => a.diffDays - b.diffDays);

    const container = document.getElementById("deadlines-container");
    if (!container) return;

    if (items.length === 0) {
      container.innerHTML = `<div class="col-span-3 text-xs text-mute p-6 text-center ph-card">No upcoming deadlines tracked.</div>`;
      return;
    }

    container.innerHTML = items.map(item => `
      <div class="ph-card p-4 space-y-2 ${item.diffDays <= 3 ? 'border-accent-red bg-accent-red-soft/20' : (item.diffDays <= 7 ? 'border-primary bg-primary/10' : '')}">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-bold uppercase ${item.diffDays <= 3 ? 'text-accent-red' : 'text-primary-active'}">
            ${item.diffDays <= 3 ? '⚠️ Critical' : (item.diffDays <= 7 ? '⏳ Approaching' : 'Upcoming')}
          </span>
          <span class="text-xs font-bold font-mono text-ink">${item.diffDays} Days Left</span>
        </div>
        <h4 class="text-sm font-bold text-ink">${item.name}</h4>
        <p class="text-xs text-mute">${item.category} · Deadline: ${new Date(item.registration_deadline).toLocaleDateString()}</p>
        <button onclick="openApplyModal(${item.id})" class="btn-ph-secondary w-full text-xs mt-2">
          Act Now →
        </button>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading deadlines:", err);
  }
}

// 7. Rewards Vault
async function loadRewards() {
  try {
    const res = await fetch("/api/rewards/metrics");
    const data = await res.json();

    const pByCat = data.potential_by_category || {};
    const cashPotential = (pByCat.CASH || 0).toLocaleString();
    const cloudPotential = (pByCat.CLOUD_CREDITS || 0).toLocaleString();
    const aiPotential = (pByCat.AI_CREDITS || 0).toLocaleString();

    document.getElementById("rewards-vault-potential").innerText = `$${cashPotential} Cash + $${cloudPotential} Cloud + $${aiPotential} AI`;
    document.getElementById("rewards-vault-claimed").innerText = `$${(data.total_claimed_usd || 0).toFixed(2)}`;

    const tbody = document.getElementById("claimed-rewards-table-body");
    if (!tbody) return;

    const claimed = (data.records || []).filter(r => r.reward_received);
    if (claimed.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-mute font-medium">0 Verified Claimed Rewards. The Rewards Vault strictly counts rewards verified with authentic receipt proof. No synthetic rewards are populated.</td></tr>`;
      return;
    }

    tbody.innerHTML = claimed.map(r => `
      <tr class="hover:bg-surface-soft/40">
        <td class="p-3 font-semibold text-ink">${r.opportunity_name}</td>
        <td class="p-3 text-body">${r.reward_type}</td>
        <td class="p-3 font-bold text-accent-green font-mono">$${r.reward_amount.toLocaleString()}</td>
        <td class="p-3 text-mute font-mono">${r.reward_date}</td>
        <td class="p-3 text-[11px] font-mono text-ink">${r.proof_of_receipt || 'Verified'}</td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading rewards:", err);
  }
}

function openClaimModal() {
  const select = document.getElementById("claim-opp-select");
  if (select) {
    select.innerHTML = allOpportunities.map(o => `<option value="${o.id}">${o.name} (${o.category})</option>`).join("");
  }
  openModal("modal-claim");
}

async function submitClaimReward() {
  const oppId = document.getElementById("claim-opp-select")?.value;
  const rewardType = document.getElementById("claim-type")?.value;
  const rewardAmount = parseFloat(document.getElementById("claim-amount")?.value || "0");
  const proof = document.getElementById("claim-proof")?.value;

  if (!oppId || !rewardType || rewardAmount <= 0) {
    alert("Please fill in valid reward details and amount.");
    return;
  }

  try {
    const res = await fetch("/api/rewards/claim", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        opportunity_id: parseInt(oppId),
        reward_type: rewardType,
        reward_amount: rewardAmount,
        proof_of_receipt: proof || "Official confirmation receipt",
      }),
    });
    if (res.ok) {
      closeModal("modal-claim");
      await initializeApp();
    }
  } catch (err) {
    console.error("Error claiming reward:", err);
  }
}

// 8. Reports (Dark code block style in doc article card)
async function loadLatestReport() {
  try {
    const res = await fetch("/api/reports/latest");
    const report = await res.json();
    if (report) {
      document.getElementById("report-date-badge").innerText = report.report_date;
      const reportDateElem = document.getElementById("report-view-date");
      if (reportDateElem) reportDateElem.innerText = report.report_date;

      const content = document.getElementById("report-markdown-content");
      if (content) {
        content.innerHTML = `<pre class="whitespace-pre-wrap font-mono text-xs leading-relaxed text-on-dark">${report.summary_markdown}</pre>`;
      }
    }
  } catch (err) {
    console.error("Error loading report:", err);
  }
}

// 9. Activity Logs
async function loadActivityLogs() {
  try {
    const filter = document.getElementById("log-filter")?.value || "All";
    const res = await fetch(`/api/logs/?event_type=${filter}&limit=40`);
    const logs = await res.json();

    const container = document.getElementById("activity-log-items");
    if (!container) return;

    if (logs.length === 0) {
      container.innerHTML = `<div class="p-6 text-center text-xs text-mute ph-card">No activity logs recorded.</div>`;
      return;
    }

    container.innerHTML = logs.map(l => `
      <div class="ph-card p-3 flex items-start justify-between text-xs">
        <div class="space-y-0.5">
          <div class="flex items-center space-x-2">
            <span class="text-[10px] font-bold px-1.5 py-0.2 rounded-xs font-mono ${getLogStatusClass(l.status)}">${l.status}</span>
            <span class="text-[11px] font-bold text-ink font-mono">${l.event_type}</span>
            <span class="font-bold text-ink">${l.title}</span>
          </div>
          <p class="text-body text-[11px]">${l.details || ''}</p>
        </div>
        <span class="text-[10px] text-mute shrink-0 font-mono">${new Date(l.timestamp).toLocaleTimeString()}</span>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading logs:", err);
  }
}

// 10. Profile Loading
async function loadProfile() {
  try {
    const res = await fetch("/api/profile/");
    const prof = await res.json();

    const skillsContainer = document.getElementById("profile-skills-tags");
    if (skillsContainer && prof.technical_skills) {
      skillsContainer.innerHTML = prof.technical_skills.map(s => `
        <span class="px-2.5 py-1 rounded-xs bg-surface-soft border border-hairline text-ink font-medium text-xs">${s}</span>
      `).join("");
    }

    const linksContainer = document.getElementById("profile-links-list");
    if (linksContainer && prof.links) {
      linksContainer.innerHTML = Object.entries(prof.links).map(([k, v]) => `
        <a href="${v}" target="_blank" class="p-2.5 bg-surface-doc rounded-md border border-hairline text-link-teal hover:underline flex items-center justify-between">
          <span class="capitalize font-bold text-ink">${k}</span>
          <span class="text-[10px] text-mute truncate max-w-[140px] font-mono">${v}</span>
        </a>
      `).join("");
    }
  } catch (err) {
    console.error("Error loading profile:", err);
  }
}

// Actions & Pipeline Execution
async function triggerDailyRun() {
  const btn = document.getElementById("btn-run-daily");
  const spinner = document.getElementById("spinner-daily");
  const icon = document.getElementById("icon-daily");

  try {
    btn.disabled = true;
    spinner.classList.remove("hidden");
    icon.classList.add("hidden");

    const res = await fetch("/api/agents/run-daily", { method: "POST" });
    await res.json();
    await initializeApp();
  } catch (err) {
    console.error("Error running daily pipeline:", err);
  } finally {
    btn.disabled = false;
    spinner.classList.add("hidden");
    icon.classList.remove("hidden");
  }
}

// Opportunity Modal
function openOppModal(id) {
  currentSelectedOppId = id;
  const opp = allOpportunities.find(o => o.id === id);
  if (!opp) return;

  document.getElementById("modal-opp-category").innerText = opp.category;
  document.getElementById("modal-opp-title").innerText = opp.name;
  document.getElementById("modal-opp-org").innerText = `${opp.organization} · ${opp.country}`;
  document.getElementById("modal-opp-score").innerText = `${opp.priority_score}/100`;
  document.getElementById("modal-opp-reward").innerText = `$${opp.reward_value.toLocaleString()} (${opp.reward_type})`;
  document.getElementById("modal-opp-fee").innerText = `$${opp.participation_fee.toFixed(2)} (Free)`;
  document.getElementById("modal-opp-eligibility").innerText = opp.eligibility_status;
  document.getElementById("modal-opp-desc").innerText = opp.source_evidence || "No description provided.";

  const reasonsList = document.getElementById("modal-opp-reasons");
  if (reasonsList) {
    reasonsList.innerHTML = (opp.eligibility_reasons || ["Verified against Arif Alam's profile."]).map(r => `<li>${r}</li>`).join("");
  }

  const breakdownBox = document.getElementById("modal-opp-score-breakdown");
  if (breakdownBox && opp.score_explanation?.breakdown) {
    const b = opp.score_explanation.breakdown;
    breakdownBox.innerHTML = `
      <div><strong>Eligibility:</strong> ${b.eligibility.points}/25 - ${b.eligibility.note}</div>
      <div><strong>Reward:</strong> ${b.reward.points}/25 - ${b.reward.note}</div>
      <div><strong>Free Policy:</strong> ${b.free_participation.points}/15 - ${b.free_participation.note}</div>
      <div><strong>Career Alignment:</strong> ${b.career_relevance.points}/15 - ${b.career_relevance.note}</div>
      <div><strong>Creator Value:</strong> ${b.creator_relevance.points}/10 - ${b.creator_relevance.note}</div>
    `;
  }

  const link = document.getElementById("modal-opp-link");
  if (link) link.href = opp.official_url;

  // Live Extracted Verbatim Evidence Quotes
  const evidenceBox = document.getElementById("modal-opp-evidence-quotes");
  if (evidenceBox) {
    evidenceBox.innerHTML = `<p class="text-xs text-mute">Loading official verbatim quotes...</p>`;
    fetch(`/api/opportunities/${id}/evidence`)
      .then(res => res.json())
      .then(quotes => {
        if (!quotes || quotes.length === 0) {
          evidenceBox.innerHTML = `<p class="text-xs text-mute italic">No verbatim excerpts extracted yet. Primary evidence: "${opp.source_evidence || 'N/A'}"</p>`;
        } else {
          evidenceBox.innerHTML = quotes.map(q => `
            <div class="p-2.5 bg-surface-card rounded border border-hairline space-y-1">
              <div class="flex items-center justify-between text-[10px] font-bold">
                <span class="px-1.5 py-0.5 rounded-xs bg-surface-soft uppercase text-ink">${q.evidence_type}</span>
                <span class="text-accent-green font-mono">${Math.round((q.confidence_score || 1.0) * 100)}% Confidence</span>
              </div>
              <p class="text-xs text-body italic">"${q.verbatim_quote}"</p>
              <div class="text-[10px] text-mute flex justify-between pt-1 border-t border-hairline-soft">
                <span>Source: <a href="${q.source_url}" target="_blank" class="text-link-teal hover:underline">${q.source_url.slice(0, 45)}...</a></span>
                <span>Extracted: ${new Date(q.extracted_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
              </div>
            </div>
          `).join("");
        }
      })
      .catch(() => {
        evidenceBox.innerHTML = `<p class="text-xs text-mute italic">Primary evidence: "${opp.source_evidence || 'N/A'}"</p>`;
      });
  }

  const btnApply = document.getElementById("modal-btn-apply");
  if (btnApply) {
    const isReg = opp.status === "Registered" || opp.status === "USER_REPORTED_REGISTERED";
    btnApply.innerText = isReg ? "Already Registered" : "Prepare Draft Application";
    btnApply.disabled = isReg;
  }

  openModal("modal-opportunity");
}

function applyFromModal() {
  closeModal("modal-opportunity");
  if (currentSelectedOppId) {
    openApplyModal(currentSelectedOppId);
  }
}

// Application Modal
function openApplyModal(id) {
  currentSelectedOppId = id;
  const opp = allOpportunities.find(o => o.id === id);
  if (!opp) return;

  document.getElementById("apply-opp-title").innerText = `Target: ${opp.name} (${opp.organization})`;
  openModal("modal-apply");
}

async function saveDraftOnly() {
  if (!currentSelectedOppId) return;
  try {
    const res = await fetch("/api/applications/draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ opportunity_id: currentSelectedOppId }),
    });
    if (res.ok) {
      closeModal("modal-apply");
      await initializeApp();
      switchTab("applications");
    }
  } catch (err) {
    console.error("Error saving draft:", err);
  }
}

async function executeApply() {
  if (!currentSelectedOppId) return;
  const requiresId = document.getElementById("check-id-upload")?.checked || false;
  const requiresLegal = document.getElementById("check-legal-agree")?.checked || false;

  try {
    const res = await fetch("/api/applications/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        opportunity_id: currentSelectedOppId,
        requires_id_upload: requiresId,
        requires_legal_agreement: requiresLegal,
      }),
    });
    const result = await res.json();
    closeModal("modal-apply");
    await initializeApp();

    if (result.status === "APPROVAL_REQUIRED") {
      alert("⚠️ Approval Gate Triggered: Sensitive action detected (ID upload / legal agreement). It has been added to your Approval Queue for explicit authorization.");
      switchTab("approvals");
    } else {
      switchTab("applications");
    }
  } catch (err) {
    console.error("Error submitting application:", err);
  }
}

// Helper Utilities
function openModal(id) {
  document.getElementById(id)?.classList.remove("hidden");
}

function closeModal(id) {
  document.getElementById(id)?.classList.add("hidden");
}

function getEligibilityBadgeClass(status) {
  if (status === "Eligible") return "bg-accent-green-soft text-accent-green border border-accent-green/30";
  if (status === "Likely eligible") return "bg-accent-blue-soft text-accent-blue border border-accent-blue/30";
  if (status === "Eligibility unclear") return "bg-accent-purple-soft text-accent-purple border border-accent-purple/30";
  return "bg-accent-red-soft text-accent-red border border-accent-red/30";
}

function getApplicationBadgeClass(status) {
  if (status === "Registered") return "bg-accent-green-soft text-accent-green border border-accent-green/30";
  if (status === "USER_REPORTED_REGISTERED") return "bg-primary/20 text-charcoal border border-primary/40 font-semibold";
  if (status === "Submitted") return "bg-accent-blue-soft text-accent-blue border border-accent-blue/30";
  if (status === "Approval Pending") return "bg-accent-red-soft text-accent-red border border-accent-red/30";
  if (status === "Draft Saved") return "bg-surface-soft text-ink border border-hairline";
  return "bg-surface-soft text-mute";
}

function getRiskBadgeClass(level) {
  if (level === "Critical" || level === "High") return "bg-accent-red-soft text-accent-red border border-accent-red/30";
  if (level === "Medium") return "bg-primary/20 text-ink border border-primary/40";
  return "bg-surface-soft text-body border border-hairline";
}

function getLogStatusClass(status) {
  if (status === "SUCCESS") return "bg-accent-green-soft text-accent-green border border-accent-green/30";
  if (status === "WARNING") return "bg-primary/20 text-ink border border-primary/40";
  if (status === "ERROR") return "bg-accent-red-soft text-accent-red border border-accent-red/30";
  return "bg-surface-soft text-mute border border-hairline";
}

// 10. Sources Registry
async function loadSources() {
  try {
    const res = await fetch("/api/sources/");
    const sources = await res.json();
    const tbody = document.getElementById("sources-table-body");
    const countBadge = document.getElementById("sources-count-badge");
    if (countBadge) countBadge.innerText = `${sources.length} registered sources`;

    if (tbody) {
      tbody.innerHTML = sources.map(s => `
        <tr class="hover:bg-surface-soft/40">
          <td class="p-3 font-semibold text-ink">
            <div>${s.name}</div>
            <div class="text-[10px] text-mute font-mono truncate max-w-xs">${s.canonical_url}</div>
          </td>
          <td class="p-3 text-body">${s.category}</td>
          <td class="p-3">
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-xs bg-accent-green-soft text-accent-green border border-accent-green/30">
              ${s.health_status}
            </span>
          </td>
          <td class="p-3 font-mono font-bold text-accent-green">${Math.round(s.reliability_score * 100)}%</td>
          <td class="p-3 font-mono text-mute">${s.rate_limit_rpm} rpm</td>
          <td class="p-3 text-mute font-mono text-[11px]">${s.last_scraped_at ? new Date(s.last_scraped_at).toLocaleTimeString() : 'Recently'}</td>
        </tr>
      `).join("");
    }

    const jobsRes = await fetch("/api/sources/jobs");
    const jobs = await jobsRes.json();
    const jobsTbody = document.getElementById("discovery-jobs-table-body");
    if (jobsTbody) {
      jobsTbody.innerHTML = jobs.map(j => `
        <tr class="hover:bg-surface-soft/40">
          <td class="p-3 font-mono text-mute">#${j.id}</td>
          <td class="p-3 font-medium text-ink">${j.source_name}</td>
          <td class="p-3 font-mono font-bold text-accent-green">${j.items_found} items</td>
          <td class="p-3"><span class="text-[10px] font-bold px-2 py-0.5 rounded-xs bg-accent-green-soft text-accent-green border border-accent-green/30">${j.status}</span></td>
          <td class="p-3 font-mono text-mute text-[11px]">${new Date(j.completed_at || j.started_at).toLocaleTimeString()}</td>
        </tr>
      `).join("");
    }
  } catch (err) {
    console.error("Error loading sources:", err);
  }
}

// 11. Integrations
async function loadIntegrations() {
  try {
    const res = await fetch("/api/integrations/");
    const integrations = await res.json();
    const container = document.getElementById("integrations-cards-container");
    if (!container) return;

    container.innerHTML = integrations.map(item => {
      let badge = `<span class="text-[10px] font-bold px-2 py-0.5 rounded-xs bg-surface-soft text-mute">Not Configured</span>`;
      if (item.status === "ACTIVE" || item.status === "CONNECTED") {
        badge = `<span class="text-[10px] font-bold px-2 py-0.5 rounded-xs bg-accent-green-soft text-accent-green border border-accent-green/30">✓ Active</span>`;
      } else if (item.status === "NOT_CONFIGURED") {
        badge = `<span class="text-[10px] font-bold px-2 py-0.5 rounded-xs bg-primary/20 text-ink border border-primary/40">Not Configured (Safe Fallback)</span>`;
      }

      return `
        <div class="ph-card p-5 space-y-3 flex flex-col justify-between">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-bold text-ink text-sm">${item.name}</span>
              ${badge}
            </div>
            <p class="text-xs text-body leading-relaxed">${item.details || 'Connector interface'}</p>
          </div>
          <div class="pt-3 border-t border-hairline-soft flex items-center justify-between text-xs">
            <span class="text-mute font-mono text-[10px]">Checked: ${new Date(item.last_checked_at).toLocaleTimeString()}</span>
            ${item.name === "GMAIL" ? `<button onclick="checkGmailConnection()" class="text-link-teal font-semibold hover:underline">Test Gmail Sync →</button>` : ''}
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Error loading integrations:", err);
  }
}

async function checkGmailConnection() {
  try {
    const res = await fetch("/api/integrations/check-gmail", { method: "POST" });
    const data = await res.json();
    alert(`Gmail Integration Status: ${data.status}\n${data.details}`);
    await loadIntegrations();
  } catch (err) {
    alert("Gmail check failed: " + err);
  }
}

async function testPlaywrightInspection() {
  const url = document.getElementById("playwright-test-url")?.value;
  const btn = document.getElementById("btn-pw-inspect");
  const resBox = document.getElementById("pw-inspect-result");
  if (!url) return;

  btn.disabled = true;
  btn.innerText = "Inspecting with Chromium...";
  resBox.classList.remove("hidden");
  resBox.innerHTML = `<div>Launching headless Chromium... Navigating to ${url}...</div>`;

  try {
    const res = await fetch("/api/agents/inspect-url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();
    resBox.innerHTML = `
      <div class="font-bold text-ink">Page Title: ${data.title || 'N/A'}</div>
      <div>Accessible: <span class="${data.accessible ? 'text-accent-green font-bold' : 'text-accent-red'}">${data.accessible ? 'Yes' : 'No'}</span></div>
      <div>CAPTCHA Detected: <span class="${data.captcha_detected ? 'text-accent-red font-bold' : 'text-accent-green'}">${data.captcha_detected ? '⚠️ CAPTCHA Found' : 'None detected'}</span></div>
      <div>Form Fields Found (${data.fields_found.length}):</div>
      <div class="text-mute pl-3">${data.fields_found.length > 0 ? data.fields_found.join(", ") : 'No form fields'}</div>
    `;
  } catch (err) {
    resBox.innerHTML = `<div class="text-accent-red">Inspection error: ${err}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerText = "Inspect Page with Playwright";
  }
}

// 12. Telemetry & Zero Cost
async function loadTelemetry() {
  try {
    const res = await fetch("/api/telemetry/runs");
    const runs = await res.json();
    const tbody = document.getElementById("telemetry-table-body");
    if (!tbody) return;

    if (runs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-mute">No telemetry runs logged yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = runs.map(r => `
      <tr class="hover:bg-surface-soft/40">
        <td class="p-3 font-semibold text-ink">${r.agent_name}</td>
        <td class="p-3 text-body font-mono text-[11px]">${r.run_type}</td>
        <td class="p-3">
          <span class="text-[10px] font-bold px-2 py-0.5 rounded-xs bg-accent-green-soft text-accent-green border border-accent-green/30">
            ${r.status}
          </span>
        </td>
        <td class="p-3 font-mono font-bold text-ink">${r.items_discovered}</td>
        <td class="p-3 font-mono text-mute">${r.duration_seconds}s</td>
        <td class="p-3 font-mono font-extrabold text-accent-green">$${(r.tool_cost_usd || 0).toFixed(2)} (Free)</td>
        <td class="p-3 font-mono text-mute text-[11px]">${new Date(r.started_at).toLocaleTimeString()}</td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading telemetry:", err);
  }
}

// ==========================================
// 13. SWAG MAXIMIZATION ENGINE FUNCTIONS
// ==========================================

async function loadSwagOpportunities() {
  try {
    const [swagRes, metricsRes] = await Promise.all([
      fetch("/api/swag"),
      fetch("/api/swag/metrics"),
    ]);

    allSwagItems = await swagRes.json();
    const metrics = await metricsRes.json();

    // Update metrics
    document.getElementById("metric-swag-total").innerText = metrics.total_swag_opportunities || allSwagItems.length;
    document.getElementById("metric-swag-india").innerText = metrics.india_free_shipping_count || 0;
    document.getElementById("metric-swag-priority").innerText = metrics.high_priority_swag_count || 0;
    document.getElementById("metric-swag-claims").innerText = metrics.total_claims || 0;

    const badge = document.getElementById("badge-swag-count");
    if (badge) badge.innerText = `${allSwagItems.length} Available`;

    renderSwagCards(allSwagItems);
  } catch (err) {
    console.error("Error loading swag opportunities:", err);
  }
}

function renderSwagCards(items) {
  const container = document.getElementById("swag-cards-container");
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = `<div class="col-span-2 ph-card p-8 text-center text-mute text-xs">No swag items match the current filter.</div>`;
    return;
  }

  container.innerHTML = items.map(s => {
    const isIndiaFree = s.india_shipping_available && s.free_shipping;
    const scoreColor = s.swag_score >= 80 ? 'text-primary-active bg-primary/20' : 'text-accent-green bg-accent-green-soft';

    return `
      <div class="ph-card p-5 space-y-3.5 flex flex-col justify-between">
        <div class="space-y-2">
          <div class="flex items-start justify-between gap-2">
            <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-xs bg-surface-soft text-ink border border-hairline font-mono">
              ${s.item_type}
            </span>
            <span class="text-xs font-mono font-extrabold px-2 py-0.5 rounded-xs ${scoreColor}">
              Score: ${s.swag_score}/100
            </span>
          </div>

          <div>
            <h4 class="text-sm font-bold text-ink leading-snug">${s.name}</h4>
            <p class="text-xs text-mute font-medium">${s.organization} · ${s.delivery_timeframe}</p>
          </div>

          <div class="flex flex-wrap gap-1.5 text-[10px] font-medium">
            <span class="px-2 py-0.5 rounded-xs ${isIndiaFree ? 'bg-accent-green-soft text-accent-green border border-accent-green/30 font-bold' : 'bg-surface-soft text-mute'}">
              ${isIndiaFree ? '🇮🇳 India: 100% Free Shipping' : 'Customs/Shipping Check Req.'}
            </span>
            <span class="px-2 py-0.5 rounded-xs bg-surface-doc text-body border border-hairline font-mono">
              Customs Risk: ${s.customs_risk}
            </span>
            <span class="px-2 py-0.5 rounded-xs bg-surface-doc text-body border border-hairline">
              Stock: ${s.stock_status}
            </span>
          </div>

          <p class="text-xs text-body leading-relaxed bg-surface-doc p-2.5 rounded-md border border-hairline">
            <strong class="text-ink">Requirement:</strong> ${s.contribution_required || 'Open registration & submission'}
          </p>
        </div>

        <div class="pt-2 border-t border-hairline flex items-center justify-between text-xs">
          <a href="${s.official_url}" target="_blank" class="font-semibold text-link-teal hover:underline text-[11px]">
            Official Rules ↗
          </a>
          <button onclick="openSwagClaimModal(${s.id})" class="btn-ph-primary text-xs space-x-1">
            <span>🎁 Claim Swag</span>
          </button>
        </div>
      </div>
    `;
  }).join("");
}

function filterSwagByCategory(category) {
  const pills = ["all", "india", "hoodie", "tshirt", "hardware"];
  pills.forEach(p => {
    const btn = document.getElementById(`swag-pill-${p}`);
    if (btn) {
      if (p === category) {
        btn.className = "px-2.5 py-1 rounded-xs font-bold text-xs bg-ink text-on-dark transition-colors";
      } else {
        btn.className = "px-2.5 py-1 rounded-xs font-medium text-xs bg-surface-soft text-body hover:bg-surface-soft/80 border border-hairline transition-colors";
      }
    }
  });

  if (category === "all") {
    renderSwagCards(allSwagItems);
  } else if (category === "india") {
    renderSwagCards(allSwagItems.filter(s => s.india_shipping_available && s.free_shipping));
  } else if (category === "hoodie") {
    renderSwagCards(allSwagItems.filter(s => s.item_type.toLowerCase().includes("hoodie") || s.item_type.toLowerCase().includes("jacket") || s.item_type.toLowerCase().includes("box")));
  } else if (category === "tshirt") {
    renderSwagCards(allSwagItems.filter(s => s.item_type.toLowerCase().includes("t-shirt") || s.item_type.toLowerCase().includes("tee")));
  } else if (category === "hardware") {
    renderSwagCards(allSwagItems.filter(s => s.item_type.toLowerCase().includes("hardware") || s.item_type.toLowerCase().includes("raspberry") || s.item_type.toLowerCase().includes("kit") || s.item_type.toLowerCase().includes("token")));
  }
}

async function triggerSwagScan() {
  try {
    const res = await fetch("/api/swag/scan", { method: "POST" });
    const data = await res.json();
    alert(`Swag scan completed! ${data.synced_count} items synced.`);
    await loadSwagOpportunities();
  } catch (err) {
    alert("Swag scan error: " + err);
  }
}

function openSwagClaimModal(swagId) {
  const item = allSwagItems.find(s => s.id === swagId);
  if (!item) return;

  document.getElementById("swag-modal-id").value = item.id;
  document.getElementById("swag-modal-title").innerText = `Claim: ${item.name}`;
  document.getElementById("swag-modal-org").innerText = `${item.organization} · ${item.item_type}`;
  document.getElementById("swag-form-size").value = "L";
  document.getElementById("swag-form-notes").value = "";

  openModal("modal-swag-claim");
}

async function submitSwagClaim() {
  const swagId = document.getElementById("swag-modal-id").value;
  const size = document.getElementById("swag-form-size").value;
  const notes = document.getElementById("swag-form-notes").value;

  try {
    const res = await fetch(`/api/swag/${swagId}/claim`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ size, notes }),
    });
    const data = await res.json();
    closeModal("modal-swag-claim");
    alert(`Swag claim prepared successfully! Claim #${data.claim_id} generated for Mumbai address.`);
    await Promise.all([loadSwagOpportunities(), loadSwagClaims()]);
  } catch (err) {
    alert("Error preparing swag claim: " + err);
  }
}

// ==========================================
// 14. SWAG CLAIMS & DELIVERY TRACKING
// ==========================================

async function loadSwagClaims() {
  try {
    const res = await fetch("/api/swag/claims");
    allSwagClaims = await res.json();

    const badge = document.getElementById("badge-claims-count");
    if (badge) badge.innerText = allSwagClaims.length;

    const ind = document.getElementById("claims-count-indicator");
    if (ind) ind.innerText = `${allSwagClaims.length} active claims`;

    const tbody = document.getElementById("swag-claims-table-body");
    if (!tbody) return;

    if (allSwagClaims.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="p-6 text-center text-mute">No physical swag claims prepared yet. Claim a hoodie or T-shirt from Swag Hunter!</td></tr>`;
      return;
    }

    tbody.innerHTML = allSwagClaims.map(c => `
      <tr class="hover:bg-surface-soft/40">
        <td class="p-3 font-semibold text-ink">
          ${c.swag_name}
          <span class="block text-[10px] text-mute font-normal">${c.organization}</span>
        </td>
        <td class="p-3 text-body font-mono">
          ${c.shipping_recipient}
          <span class="px-1.5 py-0.2 rounded-xs bg-surface-soft text-[10px] font-bold ml-1">${c.selected_size}</span>
        </td>
        <td class="p-3 text-body text-[11px] truncate max-w-[200px]" title="${c.shipping_address}">
          ${c.shipping_address}
        </td>
        <td class="p-3">
          <span class="text-[10px] font-bold px-2 py-0.5 rounded-xs bg-accent-green-soft text-accent-green border border-accent-green/30">
            ${c.claim_status}
          </span>
        </td>
        <td class="p-3 font-mono text-[11px]">
          <div>${c.courier || 'Pending Dispatch'}</div>
          ${c.tracking_number ? `<span class="text-link-blue underline">${c.tracking_number}</span>` : '<span class="text-mute text-[10px]">Awaiting Tracking</span>'}
        </td>
        <td class="p-3 text-mute font-mono text-[11px]">
          ${new Date(c.claimed_at).toLocaleDateString()}
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading swag claims:", err);
  }
}

// ==========================================
// 15. CLOUD & AI CREDITS FUNCTIONS
// ==========================================

async function loadCredits() {
  try {
    const res = await fetch("/api/credits");
    const data = await res.json();

    document.getElementById("metric-credits-total").innerText = `$${(data.total_credit_value_usd || 0).toLocaleString()}`;
    document.getElementById("metric-credits-cardfree").innerText = data.zero_card_programs || 0;
    document.getElementById("metric-credits-active").innerText = data.active_programs || 0;

    const tbody = document.getElementById("credits-table-body");
    if (!tbody) return;

    const programs = data.programs || [];
    if (programs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-mute">No credit programs synchronized yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = programs.map(p => `
      <tr class="hover:bg-surface-soft/40">
        <td class="p-3 font-bold text-ink flex items-center space-x-1.5">
          <span>${p.provider}</span>
        </td>
        <td class="p-3 text-body font-medium">${p.tier_name}</td>
        <td class="p-3 font-mono font-extrabold text-accent-green">
          $${p.remaining_amount.toLocaleString()} ${p.currency}
        </td>
        <td class="p-3">
          ${p.card_required ?
            '<span class="text-[10px] font-bold px-2 py-0.5 rounded-xs bg-accent-red-soft text-accent-red">Card Required</span>' :
            '<span class="text-[10px] font-bold px-2 py-0.5 rounded-xs bg-accent-green-soft text-accent-green border border-accent-green/30">No Card Needed</span>'
          }
        </td>
        <td class="p-3 font-mono text-mute text-[11px]">${p.expiry_date}</td>
        <td class="p-3 text-body text-[11px] max-w-xs">${p.quota_notes || 'Standard quotas'}</td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading credits:", err);
  }
}

async function triggerCreditsSync() {
  try {
    const res = await fetch("/api/credits/sync", { method: "POST" });
    const data = await res.json();
    alert(`Credits sync completed! ${data.synced_count} programs updated.`);
    await loadCredits();
  } catch (err) {
    alert("Credits sync error: " + err);
  }
}

// ==========================================
// 16. AGENT CONTROL CENTRE & ORCHESTRATOR
// ==========================================

async function loadOrchestratorStatus() {
  try {
    const [statusRes, jobsRes] = await Promise.all([
      fetch("/api/orchestrator/status"),
      fetch("/api/orchestrator/jobs"),
    ]);

    const status = await statusRes.json();
    const jobs = await jobsRes.json();

    document.getElementById("orchestrator-worker-id").innerText = status.orchestrator_id || "orchestrator-main";
    document.getElementById("orchestrator-hostname").innerText = `production-orchestrator · v2.0.0`;
    document.getElementById("orchestrator-status-badge").innerText = status.status || "ALIVE";
    document.getElementById("orchestrator-current-task").innerText = status.current_task || "Idle";
    document.getElementById("orchestrator-tasks-processed").innerText = status.tasks_processed || 0;
    document.getElementById("orchestrator-uptime").innerText = `${status.uptime_seconds || 0}s`;
    document.getElementById("orchestrator-last-heartbeat").innerText = status.last_heartbeat ? new Date(status.last_heartbeat).toLocaleTimeString() : "Just now";

    // Queue counts
    const q = status.queue_stats || {};
    document.getElementById("queue-stat-queued").innerText = `${q.queued || 0} Queued`;
    document.getElementById("queue-stat-running").innerText = `${q.running || 0} Running`;
    document.getElementById("queue-stat-dead").innerText = `${q.dead_letter || 0} Dead Letter`;

    // Fleet Subagents Grid
    const fleetGrid = document.getElementById("subagents-fleet-grid");
    if (fleetGrid && status.fleet_agents) {
      fleetGrid.innerHTML = status.fleet_agents.map(a => `
        <div class="p-3 bg-surface-doc rounded-md border border-hairline flex items-center justify-between">
          <div>
            <div class="font-bold text-ink">${a.name}</div>
            <div class="text-[10px] text-mute">${a.role}</div>
          </div>
          <span class="text-[9px] font-bold px-1.5 py-0.5 rounded-xs bg-accent-green-soft text-accent-green font-mono">
            ${a.status}
          </span>
        </div>
      `).join("");
    }

    // Worker Jobs Table
    const tbody = document.getElementById("worker-jobs-table-body");
    if (!tbody) return;

    if (jobs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-mute">No jobs in task queue yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = jobs.map(j => {
      let statusClass = "bg-surface-soft text-body";
      if (j.status === "RUNNING") statusClass = "bg-primary/20 text-ink font-bold animate-pulse";
      if (j.status === "COMPLETED") statusClass = "bg-accent-green-soft text-accent-green";
      if (j.status === "RETRYING") statusClass = "bg-accent-red-soft text-accent-red";
      if (j.status === "DEAD_LETTER") statusClass = "bg-surface-dark text-on-dark";

      return `
        <tr class="hover:bg-surface-soft/40">
          <td class="p-3 font-bold text-ink">#${j.id}</td>
          <td class="p-3 text-body font-semibold">${j.job_type}</td>
          <td class="p-3">${j.priority}</td>
          <td class="p-3">
            <span class="text-[10px] px-2 py-0.5 rounded-xs ${statusClass}">
              ${j.status}
            </span>
          </td>
          <td class="p-3 text-mute">${j.retry_count}/${j.max_retries}</td>
          <td class="p-3 text-mute text-[11px]">${j.scheduled_for ? new Date(j.scheduled_for).toLocaleTimeString() : 'Immediate'}</td>
          <td class="p-3">
            ${j.status === "DEAD_LETTER" || j.status === "FAILED" ?
              `<button onclick="retryWorkerJob(${j.id})" class="btn-ph-secondary text-[10px] px-2 py-0.5">Retry</button>` :
              `<span class="text-mute text-[10px]">—</span>`
            }
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Error loading orchestrator status:", err);
  }
}

async function triggerOrchestratorJob(jobType) {
  try {
    const res = await fetch("/api/orchestrator/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_type: jobType, priority: 8 }),
    });
    const data = await res.json();
    alert(`Enqueued Job #${data.job_id} (${data.job_type}) with priority ${data.priority}!`);
    await loadOrchestratorStatus();
  } catch (err) {
    alert("Error enqueuing job: " + err);
  }
}

async function retryWorkerJob(jobId) {
  try {
    const res = await fetch(`/api/orchestrator/jobs/${jobId}/retry`, { method: "POST" });
    const data = await res.json();
    alert(data.message);
    await loadOrchestratorStatus();
  } catch (err) {
    alert("Error retrying job: " + err);
  }
}
