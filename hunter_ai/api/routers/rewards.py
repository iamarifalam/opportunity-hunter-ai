"""
Rewards API Router
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from hunter_ai.database import get_db
from hunter_ai.agents.rewards_agent import RewardsAgent

router = APIRouter(prefix="/api/rewards", tags=["Rewards"])
rewards_agent = RewardsAgent()


class ClaimRewardRequest(BaseModel):
    opportunity_id: int
    reward_type: str
    reward_amount: float
    reward_currency: str = "USD"
    proof_of_receipt: str
    notes: Optional[str] = None


@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    metrics = await rewards_agent.get_reward_metrics(db)
    return metrics


@router.post("/claim")
async def claim_reward_endpoint(req: ClaimRewardRequest, db: AsyncSession = Depends(get_db)):
    try:
        reward = await rewards_agent.claim_reward(
            db=db,
            opportunity_id=req.opportunity_id,
            reward_type=req.reward_type,
            reward_amount=req.reward_amount,
            reward_currency=req.reward_currency,
            proof_of_receipt=req.proof_of_receipt,
            notes=req.notes or "",
        )
        return {"status": "SUCCESS", "reward": reward}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
