"""
API Router for Cloud & AI Credits Tracker.
Tracks balances, card requirements, expiration dates, and free inference tiers.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from hunter_ai.database import get_db
from hunter_ai.models import CreditBalance
from hunter_ai.agents.credits_agent import CloudCreditsAgent


router = APIRouter(prefix="/api/credits", tags=["Cloud & AI Credits"])
credits_agent = CloudCreditsAgent()


class CreditUpdateRequest(BaseModel):
    remaining_amount: float
    billing_activated: Optional[bool] = None
    quota_notes: Optional[str] = None


@router.get("", response_model=Dict[str, Any])
async def get_credits_overview(db: AsyncSession = Depends(get_db)):
    """
    Returns credit program balances and zero-card safety metrics.
    """
    return await credits_agent.get_credit_summary(db)


@router.post("/sync", response_model=Dict[str, Any])
async def sync_credits(db: AsyncSession = Depends(get_db)):
    """
    Synchronizes verified cloud and AI inference credit tiers.
    """
    synced = await credits_agent.sync_credit_programs(db)
    return {
        "status": "SUCCESS",
        "synced_count": len(synced),
        "message": f"Successfully synchronized {len(synced)} credit programs.",
    }


@router.patch("/{credit_id}", response_model=Dict[str, Any])
async def update_credit_balance(
    credit_id: int,
    body: CreditUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Updates the remaining amount or notes for an active credit program.
    """
    res = await db.execute(select(CreditBalance).where(CreditBalance.id == credit_id))
    credit = res.scalars().first()
    if not credit:
        raise HTTPException(status_code=404, detail="Credit program not found")

    credit.remaining_amount = body.remaining_amount
    if body.billing_activated is not None:
        credit.billing_activated = body.billing_activated
    if body.quota_notes:
        credit.quota_notes = body.quota_notes

    await db.commit()
    await db.refresh(credit)

    return {
        "status": "SUCCESS",
        "credit_id": credit.id,
        "provider": credit.provider,
        "remaining_amount": credit.remaining_amount,
        "billing_activated": credit.billing_activated,
    }
