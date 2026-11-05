"""
Reports API Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.database import get_db
from hunter_ai.models import DailyReport
from hunter_ai.agents.reporting_agent import ReportingAgent

router = APIRouter(prefix="/api/reports", tags=["Reports"])
reporting_agent = ReportingAgent()


@router.get("/latest")
async def get_latest_report(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DailyReport).order_by(DailyReport.created_at.desc()).limit(1))
    report = result.scalars().first()
    if not report:
        report = await reporting_agent.generate_daily_report(db)
    return report


@router.get("/")
async def list_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DailyReport).order_by(DailyReport.created_at.desc()).limit(30))
    return result.scalars().all()
