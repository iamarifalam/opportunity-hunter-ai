"""
Opportunity API Router
"""

from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.database import get_db
from hunter_ai.models import Opportunity
from hunter_ai.engines.canonical import canonicalize_url
from hunter_ai.agents.verification_agent import VerificationAgent

router = APIRouter(prefix="/api/opportunities", tags=["Opportunities"])
verification_agent = VerificationAgent()


@router.get("")
@router.get("/")
async def list_opportunities(
    category: Optional[str] = None,
    eligibility_status: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Literal["score", "deadline", "reward", "created"] = "score",
    db: AsyncSession = Depends(get_db),
):
    query = select(Opportunity)

    if category and category != "All":
        query = query.where(Opportunity.category == category)
    if eligibility_status and eligibility_status != "All":
        query = query.where(Opportunity.eligibility_status == eligibility_status)
    if status and status != "All":
        query = query.where(Opportunity.status == status)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Opportunity.name.ilike(search_pattern))
            | (Opportunity.organization.ilike(search_pattern))
            | (Opportunity.category.ilike(search_pattern))
        )

    if sort_by == "score":
        query = query.order_by(Opportunity.priority_score.desc())
    elif sort_by == "deadline":
        query = query.order_by(Opportunity.registration_deadline.asc().nulls_last())
    elif sort_by == "reward":
        query = query.order_by(Opportunity.reward_value.desc())
    else:
        query = query.order_by(Opportunity.created_at.desc())

    result = await db.execute(query)
    opportunities = result.scalars().all()
    return opportunities


@router.get("/{opportunity_id}")
async def get_opportunity(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
    opp = result.scalars().first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@router.post("/{opportunity_id}/verify")
async def verify_opportunity_endpoint(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
    opp = result.scalars().first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    verified_opp = await verification_agent.verify_opportunity(db, opp)
    return {"status": "SUCCESS", "opportunity": verified_opp}


@router.get("/{opportunity_id}/evidence")
async def get_opportunity_evidence_endpoint(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    from hunter_ai.models import Evidence
    result = await db.execute(
        select(Evidence).where(Evidence.opportunity_id == opportunity_id).order_by(Evidence.extracted_at.desc())
    )
    return result.scalars().all()

