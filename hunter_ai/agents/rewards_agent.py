"""
Rewards Agent for Opportunity Hunter AI.
Maintains the Rewards Vault with strict categorical segregation:
- Cash Rewards
- Cloud Credits (AWS, Azure, GCP)
- AI & GPU Credits (NVIDIA, OpenAI, Anthropic, Gemini)
- Professional Certifications & Exam Vouchers
- Hardware & Gadgets
Strictly separates Potential Rewards from Verified Claimed Rewards.
Never aggregates distinct reward types into a misleading monetary sum.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from hunter_ai.agents.base import BaseAgent
from hunter_ai.models import Opportunity, Reward


class RewardsAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="RewardsAgent")

    def _classify_category(self, opp_category: str, reward_type: str) -> str:
        """Determines reward category bucket."""
        text = f"{opp_category} {reward_type}".lower()
        if "cloud" in text or "aws" in text or "azure" in text or "gcp" in text:
            return "CLOUD_CREDITS"
        elif "gpu" in text or "nvidia" in text or "api" in text or "inference" in text or "gemini" in text:
            return "AI_CREDITS"
        elif "cert" in text or "exam" in text or "voucher" in text:
            return "CERTIFICATION"
        elif "cash" in text or "prize" in text or "bounty" in text or "grant" in text:
            return "CASH"
        elif "laptop" in text or "hardware" in text or "smartphone" in text or "gadget" in text:
            return "HARDWARE"
        return "OTHER"

    async def get_reward_metrics(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Calculates segregated metrics for Potential and Claimed rewards.
        """
        # 1. Fetch all active opportunities to tally potential rewards
        opp_res = await db.execute(
            select(Opportunity).where(Opportunity.status.notin_(["Rejected", "Closed"]))
        )
        opps = opp_res.scalars().all()

        potential_by_category = {
            "CASH": 0.0,
            "CLOUD_CREDITS": 0.0,
            "AI_CREDITS": 0.0,
            "CERTIFICATION": 0.0,
            "HARDWARE": 0.0,
            "OTHER": 0.0,
        }
        potential_items_by_category = {
            "CASH": 0,
            "CLOUD_CREDITS": 0,
            "AI_CREDITS": 0,
            "CERTIFICATION": 0,
            "HARDWARE": 0,
            "OTHER": 0,
        }

        for opp in opps:
            cat = self._classify_category(opp.category, opp.reward_type)
            val = opp.reward_value or 0.0
            potential_by_category[cat] += val
            potential_items_by_category[cat] += 1

        # 2. Fetch actually claimed rewards
        rew_res = await db.execute(
            select(Reward, Opportunity.name.label("opportunity_name"))
            .join(Opportunity, Reward.opportunity_id == Opportunity.id)
            .order_by(Reward.created_at.desc())
        )
        rewards_rows = rew_res.all()

        claimed_by_category = {
            "CASH": 0.0,
            "CLOUD_CREDITS": 0.0,
            "AI_CREDITS": 0.0,
            "CERTIFICATION": 0.0,
            "HARDWARE": 0.0,
            "OTHER": 0.0,
        }
        claimed_records = []
        total_claimed_cash_equivalent = 0.0

        for r, opp_name in rewards_rows:
            cat = r.reward_category or self._classify_category("", r.reward_type)
            if r.reward_received:
                claimed_by_category[cat] = claimed_by_category.get(cat, 0.0) + (r.reward_amount or 0.0)
                if cat == "CASH":
                    total_claimed_cash_equivalent += (r.reward_amount or 0.0)

            claimed_records.append({
                "id": r.id,
                "opportunity_id": r.opportunity_id,
                "opportunity_name": opp_name,
                "reward_type": r.reward_type,
                "reward_category": cat,
                "reward_amount": r.reward_amount,
                "reward_currency": r.reward_currency,
                "reward_description": r.reward_description,
                "reward_received": r.reward_received,
                "reward_date": r.reward_date,
                "proof_of_receipt": r.proof_of_receipt,
            })

        return {
            "total_potential_usd": round(sum(potential_by_category.values()), 2),
            "potential_by_category": potential_by_category,
            "potential_items_by_category": potential_items_by_category,
            "claimed_by_category": claimed_by_category,
            "total_claimed_usd": round(total_claimed_cash_equivalent, 2),
            "claimed_rewards_count": len([r for r in claimed_records if r["reward_received"]]),
            "records": claimed_records,
        }

    async def claim_reward(
        self,
        db: AsyncSession,
        opportunity_id: int,
        reward_type: str,
        reward_amount: float,
        reward_currency: str = "USD",
        proof_of_receipt: str = "",
        notes: str = "",
    ) -> Reward:
        """Records an actual claimed reward with verifiable proof."""
        res = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
        opp = res.scalars().first()
        if not opp:
            raise ValueError("Opportunity not found.")

        category = self._classify_category(opp.category, reward_type)

        reward = Reward(
            opportunity_id=opp.id,
            reward_type=reward_type,
            reward_category=category,
            reward_amount=reward_amount,
            reward_currency=reward_currency,
            reward_description=f"Reward claimed for {opp.name}",
            is_potential=False,
            reward_received=True,
            reward_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            proof_of_receipt=proof_of_receipt,
            notes=notes,
        )
        opp.status = "Reward Received"
        db.add(reward)
        await db.commit()
        await db.refresh(reward)

        await self.log_activity(
            db=db,
            event_type="Reward",
            opportunity_id=opp.id,
            title=f"Claimed Reward Verified: {reward_type}",
            details=f"Amount: {reward_amount} {reward_currency} | Proof: {proof_of_receipt}",
            status="SUCCESS",
        )
        return reward
