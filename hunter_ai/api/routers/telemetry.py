"""
Telemetry & Agent Runs API Router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.database import get_db
from hunter_ai.models import AutomationRun

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])


@router.get("/runs")
async def list_automation_runs(db: AsyncSession = Depends(get_db)):
    """Returns agent execution history with duration and zero tool costs."""
    res = await db.execute(select(AutomationRun).order_by(AutomationRun.started_at.desc()).limit(20))
    return res.scalars().all()
