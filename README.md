# 🎯 Opportunity Hunter AI
### Autonomous Personal Opportunity Agent & Swag Maximization Platform for Arif Alam

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL & SQLite](https://img.shields.io/badge/Database-Dual_Postgres_%26_SQLite-336791.svg)](#dual-database-persistence)
[![Vercel Ready](https://img.shields.io/badge/Vercel-Serverless_%2B_Cron-black.svg)](#vercel-deployment-guide)
[![Zero-Cost Guarantee](https://img.shields.io/badge/Zero--Cost-100%25_Verified_%240.00-emerald.svg)](#zero-cost--safety-policy)
[![Tests Passing](https://img.shields.io/badge/Tests-26%20Passed-brightgreen.svg)](#testing--verification)

**Opportunity Hunter AI** is an autonomous personal AI agent platform built for **Arif Alam** (AI Engineer at TCS, NMIMS Distance MBA Student, and Content Creator at *Data Science Reality*). It actively scours the web, evaluates eligibility, strictly enforces zero-cost participation ($0.00 tool cost), automates application drafts, gates sensitive actions through a human-in-the-loop security queue, maximizes developer merchandise and swag with verified 100% free delivery to India, and tracks rewards all the way to verified redemption.

---

## 🏛️ Autonomous Architecture

```mermaid
flowchart TD
    subgraph Master["1. Central Master Autonomous Orchestrator"]
        ORCH["OpportunityHunterOrchestrator\n(Worker Heartbeats · Retries · Backoff · DLQ)"]
        QUEUE[("WorkerJob Queue\nPriority 1-10 · Idempotency")]
    end

    subgraph Fleet["2. Fleet of 12 Specialized Subagents"]
        SWAG["🎁 Swag Hunter Agent\n(India Shipping · Customs Safe)"]
        HACK["💻 Hackathon Agent\n(Solo/Team · IP Retention · Pre-Reg Lock)"]
        CRED["☁️ Cloud & AI Credits Agent\n(AWS · Azure · GCP · NVIDIA · Groq)"]
        CREA["✍️ Creator Agent\n(Packt / O'Reilly Reviewer · Speaking)"]
        DISC["🌐 Global Discovery Agent\n(Devpost · GitHub Search APIs)"]
        VERI["🔍 Verification Agent\n(Official Terms & Verbatim Evidence)"]
        ELIG["🎓 Eligibility Agent\n(NMIMS MBA Student & AI Engineer Rules)"]
        SCOR["📊 Scoring Agent\n(Multi-Factor 0-100 AI Score)"]
        APPL["📝 Application Agent\n(Playwright Inspection · Profile Mapping)"]
        SECU["🛡️ Security & Cost Agent\n($0 Policy · Prompt Injection Defense)"]
        DEAD["⏰ Deadline Radar Agent\n(<3d, <7d Alerts)"]
        REWA["🏆 Rewards Claim Agent\n(Vault & Proof Verification)"]
    end

    subgraph Database["3. Dual-Database Persistence"]
        DB[("Neon / Supabase PostgreSQL\nor Local SQLite\n(22 Normalized Models)")]
    end

    subgraph Interfaces["4. Production Endpoints & UI"]
        API["FastAPI REST APIs\n(/api/swag · /api/credits · /api/orchestrator)"]
        CRON["Vercel Cron Trigger\n(Schedule: 0 2 * * * · Auth: CRON_SECRET)"]
        WORKER["Persistent Worker Host\n(scripts/run_worker.py)"]
        DASH["PostHog Sketchbook Dashboard\n(Warm Cream Canvas #eeefe9 · Hairlines · Mascots)"]
    end

    ORCH <--> QUEUE
    ORCH --> Fleet
    Fleet <--> Database
    Database <--> API
    API --> DASH
    CRON --> API
    WORKER <--> Database
```

---

## 🎁 Swag Maximization Engine (India Priority)

A dedicated, first-class engine designed to maximize physical developer merchandise delivered to Arif Alam in Mumbai, India:
- **Verified Free Shipping to India:** Items strictly verified for international courier dispatch to India via DHL, FedEx, BlueDart, or India Post.
- **Customs Duty Protection:** Evaluates customs risks (`None`, `Low`, `Medium`) and prioritizes sponsor-cleared shipments.
- **Swag Priority Score (0–100):** Weighted scoring rewarding high-tier merchandise (Hoodies, Tech Jackets, Raspberry Pi kits, Backpacks) with free shipping to India.
- **Pre-Configured Shipping Details:** Automatically maps Arif Alam's verified Mumbai address (`Bandra Kurla Complex, Mumbai, Maharashtra - 400051, India`) and preferred apparel size (`L`).
- **Physical Delivery Tracking:** Tracks claim status (`Claim Form Prepared`, `Submitted`, `In Transit`, `Delivered`) with zero fabrication guards (never marked delivered without authentic tracking receipts).

---

## 🧑‍💻 Arif Alam's Profile & Eligibility Matrix

The platform is hardcoded and calibrated around Arif Alam's authentic credentials:
- **Current Role:** AI Engineer at Tata Consultancy Services (TCS), ~4.5 years experience.
- **Location:** Mumbai, Maharashtra, India.
- **Shipping Address:** Bandra Kurla Complex, Mumbai, Maharashtra - 400051, India (Size: L).
- **Student Status:** **NMIMS Mumbai MBA in Operations & Data Science (2025–2027, Online/Distance)**.
  > **Built-in Rule:** *Treated as valid student status for student benefit & developer pack screening without re-prompting.*
- **Technical Skills:** Python, FastAPI, Docker, Kubernetes, Terraform, Jenkins, MLflow, Azure, AWS, GCP, Streamlit, LangChain, LangGraph, RAG, MCP, LLMs.
- **Content Creator Identity:** Brand: *Data Science Reality* (audience: AI Engineering, Generative AI, Community Mentoring).
- **Pre-Registered Confirmed Events (Locked against duplicate spam):**
  - *Homingo Hack Days Edition 01* (`USER_REPORTED_REGISTERED`)
  - *Arthaton 2026 AI for Finance Hackathon* (`USER_REPORTED_REGISTERED`)

---

## 🛡️ Strict Zero-Cost & Safety Policy

- **Total Tool Cost:** Exactly **$0.00**. No paid APIs, no OpenAI platform credit burn, no paid proxies.
- **Payment Gateway Detector:** Automatically rejects opportunities requiring credit cards, upfront deposits, ticketing fees, or auto-renewing subscriptions.
- **Prompt Injection Defense:** Scans and sanitizes all untrusted scraped web content before processing, neutralizing prompt injection attacks and malicious scripts.
- **Human-in-the-Loop Security Gate:** Separates safe operations (form inspection, draft creation) from sensitive actions (account creation, ID upload, legal terms acceptance, final submission) which require explicit user authorization.

---

## 🗄️ Dual-Database Persistence (SQLite + PostgreSQL)

Opportunity Hunter AI supports zero-configuration local development on SQLite and high-availability production deployment on managed PostgreSQL (Neon / Supabase):

- **Local Development:** SQLite (`hunter_ai.db`) via `sqlite+aiosqlite`.
- **Production Deployment:** Managed PostgreSQL via `postgresql+asyncpg` with connection pooling, health checks, and SSL connection parameters.
- **22 Normalized Entities:** `Opportunity`, `SwagOpportunity`, `SwagClaim`, `CreditBalance`, `WorkerHeartbeat`, `WorkerJob`, `Source`, `Evidence`, `Application`, `Confirmation`, `ApprovalRequest`, `Reward`, `Deadline`, `EligibilityAssessment`, `AutomationRun`, `ActivityLog`, `Integration`, `DiscoveryJob`, `DailyReport`, `Notification`, `UserProfileModel`.

To use PostgreSQL, simply set `DATABASE_URL` in your environment:
```bash
export DATABASE_URL="postgresql+asyncpg://user:password@ep-cool-project.neon.tech/neondb?ssl=require"
```

---

## 🚀 Vercel Deployment Guide

Opportunity Hunter AI is engineered for production deployment on Vercel:

### 1. Structure
- `api/index.py`: Exposes the ASGI FastAPI app as a Vercel Serverless Function.
- `vercel.json`: Configures Python 3.12 runtime, URL rewrites, and the daily Vercel Cron trigger.
- `frontend/`: Static PostHog-styled SPA dashboard.

### 2. Deployment Steps
```bash
# 1. Install or run Vercel CLI
npx --yes vercel

# 2. Set Production Environment Variables on Vercel:
# - DATABASE_URL: postgresql+asyncpg://... (Neon or Supabase connection string)
# - CRON_SECRET: Secure token for authenticating scheduled cron invocations
# - SESSION_SECRET: Secret for signing sessions
# - ENVIRONMENT: production

# 3. Deploy to production
npx --yes vercel --prod
```

### 3. Vercel Cron Configuration
`vercel.json` schedules daily pipeline execution at 2:00 AM UTC:
```json
{
  "crons": [
    {
      "path": "/api/cron/sync",
      "schedule": "0 2 * * *"
    }
  ]
}
```
The `/api/cron/sync` endpoint is protected by `CRON_SECRET` (sent via `Authorization: Bearer <CRON_SECRET>` header).

### 4. Background Worker Host
Because Vercel Serverless Functions are ephemeral, background tasks (Playwright form interaction, IMAP sync, long-running scrapers) run via the standalone worker host:
```bash
# Run persistently on a VPS, local machine, or container:
python scripts/run_worker.py
```
The worker continuously processes tasks from `worker_jobs` and logs live heartbeats to `worker_heartbeats`.

---

## 🧪 Testing & Verification

Opportunity Hunter AI maintains a comprehensive automated test suite verifying data integrity, zero fabrication, cost safety, and orchestrator queues:

```bash
# Run all 26 unit and integration tests:
uv run pytest

# Run specific test suites:
uv run pytest hunter_ai/tests/test_autonomous_system.py
uv run pytest hunter_ai/tests/test_api_and_pipeline.py
uv run pytest hunter_ai/tests/test_confirmation_verifier.py
```

### Test Coverage Highlights:
- ✅ **Swag Maximization Engine:** Verifies score calculation, Mumbai shipping mapping, and zero fabrication delivery guards.
- ✅ **Cloud & AI Credits:** Validates balance tracking, card requirement checks, and zero-cost safety.
- ✅ **Orchestrator & Worker:** Tests task queuing, heartbeat telemetry, and retry backoff.
- ✅ **Zero Cost & Security:** Validates prompt injection sanitization and payment rejection.
- ✅ **Duplicate Registration Lock:** Ensures Homingo and Arthaton remain locked and cannot be re-registered.

---

## 💻 Running Locally

```bash
# 1. Clone repository
git clone https://github.com/iamarifalam/hunter-ai.git
cd hunter-ai

# 2. Install dependencies with uv
uv sync

# 3. Start FastAPI server & PostHog dashboard
./scripts/run_server.sh
# Open http://localhost:8000 in your browser

# 4. In a separate terminal, start the background worker:
python scripts/run_worker.py
```
