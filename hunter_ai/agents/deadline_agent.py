"""
Deadline Agent for Opportunity Hunter AI.
Monitors all registration and submission deadlines.
Categorizes impending urgency:
- Critical (<3 days)
- Approaching (<7 days)
- Normal (>7 days)
- Expired (automatically marks opportunities as Closed)
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.agents.base import BaseAgent
from hunter_ai.models import Opportunity, Deadline


class DeadlineAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="DeadlineAgent")

    async def check_deadlines(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Scans all opportunities and evaluates deadline urgency.
        Updates status to Closed for expired events.
        """
        now = datetime.now(timezone.utc)
        result = await db.execute(select(Opportunity))
        opportunities = result.scalars().all()

        critical: List[Dict[str, Any]] = []
        approaching: List[Dict[str, Any]] = []
        upcoming: List[Dict[str, Any]] = []
        expired_count = 0

        for opp in opportunities:
            # Check registration deadline
            deadline_str = opp.registration_deadline or opp.submission_deadline
            if not deadline_str:
                continue

            try:
                dt = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                delta_days = (dt - now).total_seconds() / 86400.0

                item_info = {
                    "id": opp.id,
                    "name": opp.name,
                    "category": opp.category,
                    "deadline": deadline_str,
                    "days_remaining": round(delta_days, 1),
                    "status": opp.status,
                }

                urgency = "NORMAL"
                if delta_days < 0:
                    expired_count += 1
                    urgency = "EXPIRED"
                    if opp.status not in ["Registered", "USER_REPORTED_REGISTERED", "Reward Received"]:
                        opp.status = "Closed"
                elif delta_days <= 3.0:
                    urgency = "URGENT_3D"
                    critical.append(item_info)
                elif delta_days <= 7.0:
                    urgency = "APPROACHING_7D"
                    approaching.append(item_info)
                else:
                    upcoming.append(item_info)

                # Upsert into Deadlines table
                dl_res = await db.execute(select(Deadline).where(Deadline.opportunity_id == opp.id))
                dl = dl_res.scalars().first()
                if not dl:
                    dl = Deadline(
                        opportunity_id=opp.id,
                        deadline_type="REGISTRATION" if opp.registration_deadline else "SUBMISSION",
                        deadline_timestamp=deadline_str,
                        urgency=urgency,
                        is_passed=(delta_days < 0),
                        verified_via=opp.official_url,
                    )
                    db.add(dl)
                else:
                    dl.urgency = urgency
                    dl.is_passed = (delta_days < 0)

            except Exception:
                continue

        await db.commit()

        await self.log_activity(
            db=db,
            event_type="Scheduler",
            title=f"Deadline Radar Scan: {len(critical)} Critical (<3d), {len(approaching)} Approaching (<7d)",
            details=f"Expired opportunities marked closed: {expired_count}.",
            status="INFO",
        )

        return {
            "critical_count": len(critical),
            "critical_items": critical,
            "approaching_count": len(approaching),
            "approaching_items": approaching,
            "upcoming_count": len(upcoming),
            "expired_count": expired_count,
        }
