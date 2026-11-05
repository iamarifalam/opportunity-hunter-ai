"""
Eligibility Agent for Opportunity Hunter AI.
Compares opportunity terms directly against Arif Alam's background:
- TCS AI Engineer (~4.5 yrs exp)
- NMIMS Mumbai distance MBA (valid student screening status)
- Location: India
- Skills & Content Creator profile
"""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.agents.base import BaseAgent
from hunter_ai.engines.eligibility import evaluate_eligibility
from hunter_ai.models import Opportunity, EligibilityAssessment
from hunter_ai.profile_data import USER_PROFILE


class EligibilityAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="EligibilityAgent")

    async def evaluate_all(self, db: AsyncSession) -> List[Opportunity]:
        """Evaluates eligibility for all stored opportunities."""
        result = await db.execute(select(Opportunity))
        opportunities = result.scalars().all()

        evaluated_list = []
        for opp in opportunities:
            opp_dict = {
                "name": opp.name,
                "category": opp.category,
                "country": opp.country,
                "required_skills": opp.required_skills or [],
                "registration_deadline": opp.registration_deadline,
                "description": opp.source_evidence or "",
            }

            status, reasons = evaluate_eligibility(opp_dict, USER_PROFILE)
            opp.eligibility_status = status
            opp.eligibility_reasons = reasons

            # Advance workflow status if appropriate and not already in advanced workflow state
            if opp.status not in ["Registered", "USER_REPORTED_REGISTERED", "Submitted", "Draft Saved", "Approval Required", "Closed", "Rejected"]:
                if status in ["Eligible", "Likely eligible"]:
                    opp.status = "Eligible"
                elif status == "Not eligible":
                    opp.status = "Rejected"

            # Record or update EligibilityAssessment
            res_ass = await db.execute(select(EligibilityAssessment).where(EligibilityAssessment.opportunity_id == opp.id))
            ass = res_ass.scalars().first()
            if not ass:
                ass = EligibilityAssessment(
                    opportunity_id=opp.id,
                    country_eligible=True,
                    student_eligible=True,
                    professional_eligible=True,
                    skills_matched=opp.required_skills or [],
                    fee_free=(opp.participation_fee == 0.0),
                    overall_verdict=status,
                    reasoning={"reasons": reasons},
                )
                db.add(ass)
            else:
                ass.overall_verdict = status
                ass.reasoning = {"reasons": reasons}

            evaluated_list.append(opp)

        await db.commit()

        await self.log_activity(
            db=db,
            event_type="Eligibility",
            title=f"Eligibility evaluation completed for {len(evaluated_list)} opportunities",
            details="Profile checked: India residence, NMIMS distance MBA student status, TCS AI Engineer credentials.",
            status="SUCCESS",
        )

        return evaluated_list
