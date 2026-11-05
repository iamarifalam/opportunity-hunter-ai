# Opportunity Hunter AI — Technical Audit & Production Reality Assessment

**Audit Date:** 2026-11-05  
**Auditor:** Antigravity Senior AI Systems Engineer  
**Target:** Opportunity Hunter AI Repository (`/Users/apple/Downloads/hunter ai`)

---

## 1. Repository & Technology Stack Identification

| Component | Technology | Version / Details | Status |
|---|---|---|---|
| **Backend Runtime** | Python (CPython) | 3.12.13 (via uv virtualenv `.venv`) | Production Ready |
| **Backend Framework** | FastAPI + Uvicorn | `fastapi==0.162.0`, `uvicorn==0.54.0` | Production Ready |
| **Database Engine** | SQLite with AsyncIO | `aiosqlite==0.22.1`, `SQLAlchemy==2.1.8` | Good for single-node; needs relational schema expansion |
| **Browser Automation** | Playwright Chromium | `playwright==1.64.1` with Chromium v1248 | Installed & functional headless engine |
| **Scheduler** | APScheduler | `apscheduler==3.11.3` (CronTrigger Asia/Kolkata) | Running background loop |
| **Testing** | Pytest + pytest-asyncio | `pytest==9.2.0`, `pytest-asyncio==1.4.1.post1` | 21 passing synthetic tests |
| **Frontend Framework** | Vanilla JS SPA + Tailwind CDN + PostHog Design Tokens | Embedded SPA at `frontend/index.html` + `frontend/js/app.js` | Needs removal of static assumptions & wiring to real endpoints |

---

## 2. Inventory of Fabricated Data & False Metrics (Must Be Removed)

### 🚨 Critical Audit Findings

1. **Hardcoded Opportunity Catalog (`hunter_ai/agents/discovery_agent.py`):**
   - Contains `AUTHENTIC_OPPORTUNITY_CATALOG` with 18 hardcoded dictionary definitions (e.g., *Google Gemini API Developer Competition*, *Homingo Hack Days*, *Arthaton 2026*, *AWS Activate*, *NVIDIA Inception*, *Packt Reviewer*).
   - **Flaw:** None of these records were discovered by a live scraper or verified against live web evidence. They were static dictionary literals inserted into the SQLite database on startup.
   
2. **Manufactured Confirmation Receipts (`hunter_ai/profile_data.py` & `hunter_ai/agents/verification_agent.py`):**
   - Hardcoded synthetic tokens: `Registration ID #HMD-2026-ARIF` and `Team Registration ID #ARTH-AI-9942`.
   - **Flaw:** Neither Gmail OAuth nor IMAP was actually called to verify these emails. The code blindly marked them `Registered` with a manufactured confirmation string. Per user instruction, these must be `USER_REPORTED_REGISTERED` until real Gmail confirmation evidence is authenticated.

3. **Manufactured Reward Claims (`hunter_ai/seed_data.py`):**
   - Automatically claimed $165 for *Microsoft Learn Cloud Skills Challenge* with a synthetic voucher code `MSFT-AI102-ARIF-9942`.
   - **Flaw:** Fake reward claim created to inflate dashboard numbers. This violates the zero-fabrication mandate.

4. **Misleading Aggregate Metrics (`$345,810` Potential / `$165` Claimed):**
   - Sums cash prizes, cloud credits, and certification voucher face values into one single arbitrary monetary number (`$345,810`).
   - **Flaw:** Incomparable reward types (credits vs cash vs exam waivers) cannot be merged into an inflated total. They must be tracked in distinct categories (Cash, Cloud Credits, API Credits, GPU Credits, Certifications, Hardware).

5. **Lifespan Auto-Seeder (`hunter_ai/api/app.py`):**
   - The FastAPI lifespan hook ran `coordinator.run_full_pipeline(session)` on every boot, auto-inserting the static 18 items into `hunter_ai.db`.
   - **Flaw:** Contaminates a clean production database on startup with synthetic data.

---

## 3. Database Schema Evaluation

The current SQLite database (`hunter_ai/models/__init__.py`) has only 7 tables:
- `opportunities`
- `applications`
- `rewards`
- `approval_requests`
- `activity_logs`
- `daily_reports`
- `user_profiles`

### Missing Relational Structures Required for Production Reality:
- ❌ **`sources`:** Registry of live opportunity sources (Devpost, GitHub, HackerEarth, Kaggle, HuggingFace, AWS, Microsoft) with URL, health score, reliability rating, error count, and last scraped timestamp.
- ❌ **`evidence`:** Granular evidence records linking opportunities to exact text excerpts, source URLs, confidence scores, and extraction timestamps.
- ❌ **`eligibility_assessments`:** Rule-by-rule matching evidence (Country, Student, Professional, Skills, Fee).
- ❌ **`confirmations`:** Authenticated email confirmation receipts with raw headers, message ID, timestamp, and verification status.
- ❌ **`deadlines`:** Structured multi-date tracking (registration cutoff, draft deadline, submission deadline, prize award date).
- ❌ **`automation_runs`:** Track autonomous agent executions with tool usage, duration, errors, and tool cost accounting.
- ❌ **`integrations`:** Real account connections (Gmail OAuth/IMAP, GitHub API token, Playwright browser health).
- ❌ **`discovery_jobs`:** Live scraping queue and execution log.

---

## 4. API Endpoints Audit

| Endpoint | Method | Current Functionality | Reality Assessment |
|---|---|---|---|
| `/health` | GET | Returns status & user | Functional |
| `/api/opportunities/` | GET, POST | Queries SQLite table | Reads database, but data was seeded synthetically |
| `/api/opportunities/{id}` | GET | Returns single opportunity | Functional |
| `/api/opportunities/{id}/verify` | POST | Calls `verification_agent` | Mostly stub logic without real web extraction |
| `/api/applications/` | GET | Queries applications | Functional |
| `/api/applications/draft` | POST | Maps profile to draft | Functional local mapper |
| `/api/applications/submit` | POST | Triggers approval gate | Functional security checkpoint |
| `/api/approvals/` | GET | Returns approval requests | Functional |
| `/api/approvals/{id}/action` | POST | Authorizes or rejects action | Functional |
| `/api/rewards/metrics` | GET | Aggregates rewards | Lumps all reward types together; needs breakdown |
| `/api/rewards/claim` | POST | Adds claimed reward | Functional |
| `/api/profile/` | GET, PUT | Reads/writes user profile | Functional |
| `/api/logs/` | GET | Activity audit logs | Functional |
| `/api/reports/` | GET | Daily reports | Functional |
| `/api/agents/run-daily` | POST | Triggers coordinator | Functional pipeline runner, but inputs were static |
| `/api/agents/discover` | POST | Triggers discovery | Pulled from hardcoded catalog |
| `/api/agents/inspect-url` | POST | Playwright page inspector | Functional real browser crawler |

---

## 5. Browser Automation & Integrations Audit

- **Playwright:** Browser engine is properly installed (`.venv/bin/playwright install chromium` downloaded Chromium 1248). Playwright code in `RegistrationAgent.inspect_page_with_playwright` works and correctly detects CAPTCHAs and inputs.
- **Gmail Integration:** Missing live connection. It was simulated using string literals. Must implement real Gmail connector interface (supporting OAuth2 / App Passwords) with graceful unconfigured fallback to `USER_REPORTED_REGISTERED`.
- **Live Scraping Engine:** Currently lacks dynamic source crawlers (Devpost, GitHub API, HackerEarth, Unstop, RSS feeds).

---

## 6. Action Plan for Production Reality Rebuild

1. **Wipe Out Fabricated Data:**
   - Drop synthetic seed arrays from discovery.
   - Clean out fake claims and manufactured confirmation IDs.
   - Set true default state: 0 fake opportunities, 0 fake rewards.
2. **Expand Database Schema to 14 Relational Models:**
   - Add `sources`, `evidence`, `eligibility_assessments`, `confirmations`, `deadlines`, `automation_runs`, `integrations`, `discovery_jobs`.
3. **Implement Live Dynamic Multi-Source Discovery:**
   - Connect live GitHub Competitions API & Grant feeds.
   - Connect Devpost public hackathons feed.
   - Connect HackerEarth public challenges scraper.
   - Connect Hugging Face competitions API.
   - Connect Official Cloud Provider developer grants (AWS, Azure, NVIDIA, GCP).
4. **Implement Deterministic Evidence Extractor:**
   - Real HTTP retrieval via `httpx`.
   - Text parsing and exact excerpt extraction for fees, eligibility, and deadlines.
   - Status classifications: `VERIFIED`, `PARTIALLY_VERIFIED`, `UNVERIFIED`, `EXPIRED`, `CLOSED`, `NOT_ELIGIBLE`, `BLOCKED_BY_COST`.
5. **Implement Categorized Reward Ledger:**
   - Separate Cash, Cloud Credits, API Credits, GPU Credits, Certifications, Hardware.
   - Separate Potential, Awarded, Claimed, and Received.
6. **Implement Full 13-Agent Architecture:**
   - Modular Python agents with real execution logs and zero-cost tool accounting.
7. **Redesign Dashboard around Real Evidence:**
   - 18 complete functional views including Source Registry, Agent Control Centre, Evidence Modal, and Deadline Calendar.
   - Real calculated metrics; no static mockups.
