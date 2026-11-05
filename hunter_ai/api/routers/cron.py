"""
Vercel Cron Endpoint for Opportunity Hunter AI.
Protected by CRON_SECRET token. Triggers scheduled discovery, verification, and deadline sweeps.
"""

import os
from typing import Dict, Any
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from hunter_ai.database import get_db
from hunter_ai.agents.orchestrator import OpportunityHunterOrchestrator


router = APIRouter(prefix="/api/cron", tags=["Vercel Cron"])
orchestrator = OpportunityHunterOrchestrator(worker_id="vercel-cron-worker")


def verify_cron_secret(authorization: str = Header(None), x_cron_secret: str = Header(None)):
    """
    Validates CRON_SECRET against environment configuration if set.
    """
    configured_secret = os.getenv("CRON_SECRET")
    if not configured_secret:
        # In local/development mode without CRON_SECRET, permit invocation
        return True

    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split("Bearer ")[-1].strip()
    elif x_cron_secret:
        auth_token = x_cron_secret.strip()

    if auth_token != configured_secret:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid CRON_SECRET")
    return True


@router.get("/sync", response_model=Dict[str, Any])
@router.post("/sync", response_model=Dict[str, Any])
async def cron_sync(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorized: bool = Depends(verify_cron_secret),
):
    """
    Vercel Cron entrypoint. Triggers full autonomous discovery & audit cycle.
    """
    cycle_result = await orchestrator.run_full_autonomous_cycle(db)
    return {
        "status": "SUCCESS",
        "invoked_via": "VERCEL_CRON",
        "result": cycle_result,
    }
