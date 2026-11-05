"""
Agents Control & Execution API Router
"""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from hunter_ai.database import get_db
from hunter_ai.agents.coordinator import AgentCoordinator
from hunter_ai.agents.registration_agent import RegistrationAgent

router = APIRouter(prefix="/api/agents", tags=["Agents"])
coordinator = AgentCoordinator()
registration_agent = RegistrationAgent()


class InspectUrlRequest(BaseModel):
    url: str


@router.post("/run-daily")
async def trigger_daily_run(db: AsyncSession = Depends(get_db)):
    """Manually triggers the full multi-agent pipeline immediately."""
    result = await coordinator.run_full_pipeline(db)
    return {"status": "SUCCESS", "result": result}


@router.post("/discover")
async def trigger_discovery(db: AsyncSession = Depends(get_db)):
    """Triggers discovery agent specifically."""
    discovered = await coordinator.discovery_agent.run_discovery(db)
    await coordinator.verification_agent.verify_all_active(db)
    await coordinator.eligibility_agent.evaluate_all(db)
    await coordinator.scoring_agent.score_all(db)
    return {
        "status": "SUCCESS",
        "discovered_count": len(discovered),
    }


@router.post("/inspect-url")
async def inspect_url(req: InspectUrlRequest):
    """Uses Playwright to safely inspect registration page for CAPTCHAs and forms."""
    inspection = await registration_agent.inspect_page_with_playwright(req.url)
    return inspection
