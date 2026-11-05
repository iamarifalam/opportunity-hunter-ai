"""
Evidence API Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.database import get_db
from hunter_ai.models import Evidence, Opportunity

router = APIRouter(prefix="/api/evidence", tags=["Evidence"])


@router.get("/")
async def list_recent_evidence(db: AsyncSession = Depends(get_db)):
    """Returns recent verified verbatim evidence quotes."""
    res = await db.execute(
        select(Evidence, Opportunity.name.label("opportunity_name"))
        .join(Opportunity, Evidence.opportunity_id == Opportunity.id)
        .order_by(Evidence.extracted_at.desc())
        .limit(30)
    )
    rows = res.all()
    results = []
    for ev, opp_name in rows:
        results.append({
            "id": ev.id,
            "opportunity_id": ev.opportunity_id,
            "opportunity_name": opp_name,
            "evidence_type": ev.evidence_type,
            "verbatim_quote": ev.verbatim_quote,
            "source_url": ev.source_url,
            "confidence_score": ev.confidence_score,
            "is_verified": ev.is_verified,
            "extracted_at": ev.extracted_at,
        })
    return results


@router.get("/opportunity/{opportunity_id}")
async def get_opportunity_evidence(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    """Returns all evidence items for a given opportunity."""
    res = await db.execute(
        select(Evidence).where(Evidence.opportunity_id == opportunity_id).order_by(Evidence.extracted_at.desc())
    )
    return res.scalars().all()
