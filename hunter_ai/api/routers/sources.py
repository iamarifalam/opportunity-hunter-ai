"""
Sources Registry API Router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.database import get_db
from hunter_ai.models import Source, DiscoveryJob

router = APIRouter(prefix="/api/sources", tags=["Sources"])


@router.get("/")
async def list_sources(db: AsyncSession = Depends(get_db)):
    """Returns registered opportunity sources with health and reliability ratings."""
    res = await db.execute(select(Source).order_by(Source.reliability_score.desc()))
    return res.scalars().all()


@router.get("/jobs")
async def list_discovery_jobs(db: AsyncSession = Depends(get_db)):
    """Returns recent discovery job executions."""
    res = await db.execute(select(DiscoveryJob).order_by(DiscoveryJob.started_at.desc()).limit(20))
    return res.scalars().all()
