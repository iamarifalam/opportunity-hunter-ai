"""
Scoring Agent for Opportunity Hunter AI.
Ranks opportunities from 0-100 based on eligibility match, reward value,
zero-cost guarantee, AI career relevance, and Data Science Reality creator alignment.
"""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.agents.base import BaseAgent
from hunter_ai.engines.scoring import calculate_opportunity_score
from hunter_ai.models import Opportunity


class ScoringAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ScoringAgent")

    async def score_all(self, db: AsyncSession) -> List[Opportunity]:
        """Calculates AI priority score and explanation for all opportunities."""
        result = await db.execute(select(Opportunity))
        opportunities = result.scalars().all()

        scored_list = []
        for opp in opportunities:
            opp_dict = {
                "name": opp.name,
                "category": opp.category,
                "organization": opp.organization,
                "reward_value": opp.reward_value,
                "reward_type": opp.reward_type,
                "participation_fee": opp.participation_fee,
                "description": opp.source_evidence or "",
                "registration_deadline": opp.registration_deadline,
            }

            score, explanation = calculate_opportunity_score(
                opportunity_data=opp_dict,
                eligibility_status=opp.eligibility_status,
            )

            opp.priority_score = score
            opp.score_explanation = explanation
            scored_list.append(opp)

        await db.commit()

        await self.log_activity(
            db=db,
            event_type="Scoring",
            title=f"AI Scoring completed for {len(scored_list)} opportunities",
            details="Scored on a 0-100 scale: Cash, GPU/Cloud credits, AI Certs, and Agentic relevance weighted.",
            status="SUCCESS",
        )

        return scored_list
