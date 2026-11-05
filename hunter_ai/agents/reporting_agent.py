"""
Reporting Agent for Opportunity Hunter AI.
Generates concise, actionable Daily Briefings and executive summaries
for Arif Alam's daily automation cycle.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from hunter_ai.agents.base import BaseAgent
from hunter_ai.models import Opportunity, Application, Reward, DailyReport, ApprovalRequest


class ReportingAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ReportingAgent")

    async def generate_daily_report(self, db: AsyncSession) -> DailyReport:
        """
        Synthesizes metrics, newly discovered items, high-priority matches,
        approaching deadlines, and approval requests into a comprehensive report.
        """
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Counts
        total_discovered = (await db.execute(select(func.count(Opportunity.id)))).scalar() or 0
        verified_count = (await db.execute(select(func.count(Opportunity.id)).where(Opportunity.status != "Discovered"))).scalar() or 0
        eligible_count = (await db.execute(select(func.count(Opportunity.id)).where(Opportunity.eligibility_status.in_(["Eligible", "Likely eligible"])))).scalar() or 0
        
        # Deadlines approaching (<7 days)
        now_dt = datetime.now(timezone.utc)
        opps = (await db.execute(select(Opportunity).where(Opportunity.status.notin_(["Closed", "Rejected"])))).scalars().all()
        
        approaching_deadlines = []
        for o in opps:
            if o.registration_deadline:
                try:
                    dt = datetime.fromisoformat(o.registration_deadline.replace("Z", "+00:00"))
                    days = (dt - now_dt).total_seconds() / 86400.0
                    if 0 < days <= 7:
                        approaching_deadlines.append(f"{o.name} ({int(days)}d left)")
                except Exception:
                    pass

        # Top 3 High Priority Recommendations
        top_opps = (await db.execute(
            select(Opportunity)
            .where(Opportunity.status.notin_(["Closed", "Rejected"]))
            .order_by(Opportunity.priority_score.desc())
            .limit(4)
        )).scalars().all()

        # Rewards via RewardsAgent for segregated accounting
        from hunter_ai.agents.rewards_agent import RewardsAgent
        reward_metrics = await RewardsAgent().get_reward_metrics(db)
        potential_by_cat = reward_metrics["potential_by_category"]
        claimed_by_cat = reward_metrics["claimed_by_category"]
        claimed_total = reward_metrics["total_claimed_usd"]
        claimed_count = reward_metrics["claimed_rewards_count"]

        # Pending approvals
        pending_approvals = (await db.execute(select(func.count(ApprovalRequest.id)).where(ApprovalRequest.status == "Pending"))).scalar() or 0

        # Build Markdown summary
        md = f"""# 🎯 Opportunity Hunter AI — Daily Executive Brief
**Date:** {today_str} | **Prepared for:** Arif Alam (AI Engineer · Content Creator)

### 📊 Key Health & Discovery Metrics
- **Total Opportunities Discovered:** {total_discovered}
- **Verified Legitimate Opportunities:** {verified_count}
- **Verified Eligible for Profile:** {eligible_count}
- **Upcoming Deadlines (< 7 days):** {len(approaching_deadlines)}
- **Pending Approvals in Queue:** {pending_approvals}

### 💎 Segregated Potential Value by Category
- **Cash Prizes & Bounties:** ${potential_by_cat['CASH']:,.2f}
- **Cloud Infrastructure Credits (AWS, Azure, GCP):** ${potential_by_cat['CLOUD_CREDITS']:,.2f}
- **AI & GPU Credits (NVIDIA, Gemini):** ${potential_by_cat['AI_CREDITS']:,.2f}
- **Professional Certifications:** {reward_metrics['potential_items_by_category']['CERTIFICATION']} programs
- **Actually Claimed / Received:** ${claimed_total:,.2f} ({claimed_count} claimed receipts)

---

### 🌟 Top Recommended Opportunities for You
"""
        highlights = []
        for t in top_opps:
            highlights.append({
                "id": t.id,
                "name": t.name,
                "score": t.priority_score,
                "reward": f"{t.reward_type} (${t.reward_value:,.0f})",
                "deadline": t.registration_deadline or "Ongoing",
            })
            md += f"- **[{t.priority_score}/100] {t.name}** ({t.category})\n"
            md += f"  - *Reward:* {t.reward_type} (${t.reward_value:,.0f}) | *Fee:* $0.00 (Free)\n"
            md += f"  - *Reasoning:* {t.score_explanation.get('summary', 'Top match')}\n"

        if approaching_deadlines:
            md += "\n### ⏳ Impending Deadlines Requiring Action\n"
            for d in approaching_deadlines:
                md += f"- ⚠️ **{d}**\n"

        if pending_approvals > 0:
            md += f"\n### 🛡️ Safety & Approval Radar\n"
            md += f"- There are **{pending_approvals} pending approval requests** requiring your explicit review before proceeding.\n"

        md += "\n*Generated automatically by Opportunity Hunter AI Daily Automation.*"

        # Check existing report for today
        res = await db.execute(select(DailyReport).where(DailyReport.report_date == today_str))
        report = res.scalars().first()
        if not report:
            report = DailyReport(
                report_date=today_str,
                total_discovered=total_discovered,
                verified_count=verified_count,
                eligible_count=eligible_count,
                approaching_deadlines_count=len(approaching_deadlines),
                potential_reward_total=potential_by_cat.get("CASH", 0.0),
                claimed_reward_total=claimed_total,
                categorized_rewards_json=reward_metrics,
                highlights_json=highlights,
                summary_markdown=md,
            )
            db.add(report)
        else:
            report.total_discovered = total_discovered
            report.verified_count = verified_count
            report.eligible_count = eligible_count
            report.approaching_deadlines_count = len(approaching_deadlines)
            report.potential_reward_total = potential_by_cat.get("CASH", 0.0)
            report.claimed_reward_total = claimed_total
            report.categorized_rewards_json = reward_metrics
            report.highlights_json = highlights
            report.summary_markdown = md

        await db.commit()
        await db.refresh(report)

        await self.log_activity(
            db=db,
            event_type="Scheduler",
            title=f"Daily Briefing Generated for {today_str}",
            details=f"Identified {len(highlights)} top recommendations, {len(approaching_deadlines)} approaching deadlines.",
            status="SUCCESS",
        )

        return report
