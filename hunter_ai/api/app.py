"""
Main FastAPI Application for Opportunity Hunter AI.
Provides REST APIs, background scheduler integration, and serves the dashboard UI.
"""

from contextlib import asynccontextmanager
from pathlib import Path
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from hunter_ai.config import settings
from hunter_ai.database import init_db, AsyncSessionLocal
from hunter_ai.scheduler.daily_job import start_scheduler, shutdown_scheduler
from hunter_ai.agents.orchestrator import OpportunityHunterOrchestrator
from hunter_ai.api.routers import (
    opportunities,
    applications,
    approvals,
    rewards,
    profile,
    logs,
    reports,
    agents,
    sources,
    evidence,
    integrations,
    telemetry,
    swag,
    credits,
    orchestrator as orchestrator_router,
    cron,
)

from hunter_ai.models import Opportunity
from hunter_ai.agents.swag_agent import SwagHunterAgent
from hunter_ai.agents.credits_agent import CloudCreditsAgent
from hunter_ai.agents.hackathon_agent import HackathonAgent
from hunter_ai.agents.creator_agent import CreatorAgent
from sqlalchemy import select

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database
    print("⚡ [Hunter AI] Initializing database (SQLite / PostgreSQL dual mode)...")
    await init_db()

    # Pre-seed initial verified discovery if database is completely empty
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Opportunity).limit(1))
        existing_opp = res.scalars().first()
        if not existing_opp:
            print("🔍 [Hunter AI] Fresh database detected. Syncing verified opportunity registries...")
            swag_agent = SwagHunterAgent()
            await swag_agent.scan_and_sync_swag(session)
            cred_agent = CloudCreditsAgent()
            await cred_agent.sync_credit_programs(session)
            hack_agent = HackathonAgent()
            await hack_agent.sync_hackathons(session)
            creator_agent = CreatorAgent()
            await creator_agent.sync_creator_opportunities(session)

            if not (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")):
                master_orchestrator = OpportunityHunterOrchestrator()
                await master_orchestrator.run_full_autonomous_cycle(session)
        else:
            # Sync verified swag items and credits without blocking on external search APIs
            swag_agent = SwagHunterAgent()
            await swag_agent.scan_and_sync_swag(session)
            cred_agent = CloudCreditsAgent()
            await cred_agent.sync_credit_programs(session)

    print("✅ [Hunter AI] Database tables verified, swag engine & verified opportunities synced.")

    # Start daily background scheduler (only in persistent server mode, not ephemeral serverless)
    if not (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")):
        start_scheduler()

    yield

    # Shutdown
    if not (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")):
        shutdown_scheduler()
    print("🛑 [Hunter AI] Application shutdown completed.")


app = FastAPI(
    title="Opportunity Hunter AI",
    description="Autonomous Personal Opportunity Agent Platform for Arif Alam",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(opportunities.router)
app.include_router(applications.router)
app.include_router(approvals.router)
app.include_router(rewards.router)
app.include_router(profile.router)
app.include_router(logs.router)
app.include_router(reports.router)
app.include_router(agents.router)
app.include_router(sources.router)
app.include_router(evidence.router)
app.include_router(integrations.router)
app.include_router(telemetry.router)
app.include_router(swag.router)
app.include_router(credits.router)
app.include_router(orchestrator_router.router)
app.include_router(cron.router)


@app.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "service": "Opportunity Hunter AI",
        "version": "2.0.0",
        "user": "Arif Alam",
        "mode": "Autonomous Production System",
    }


# Mount Static Frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{catchall:path}")
    async def serve_spa(catchall: str):
        file_path = FRONTEND_DIR / catchall
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIR / "index.html")
