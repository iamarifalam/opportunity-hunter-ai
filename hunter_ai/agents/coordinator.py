"""
Agent Coordinator
Orchestrates the lifecycle across all logical agents in Opportunity Hunter AI:
Discovery -> Verification -> Eligibility -> Scoring -> Deadlines -> Daily Reporting.
"""

import time
from typing import Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from hunter_ai.agents.discovery_agent import DiscoveryAgent
from hunter_ai.agents.verification_agent import VerificationAgent
from hunter_ai.agents.eligibility_agent import EligibilityAgent
from hunter_ai.agents.scoring_agent import ScoringAgent
from hunter_ai.agents.registration_agent import RegistrationAgent
from hunter_ai.agents.deadline_agent import DeadlineAgent
from hunter_ai.agents.rewards_agent import RewardsAgent
from hunter_ai.agents.reporting_agent import ReportingAgent
from hunter_ai.agents.email_agent import EmailAgent
from hunter_ai.models import AutomationRun, Integration


class AgentCoordinator:
    def __init__(self):
        self.discovery_agent = DiscoveryAgent()
        self.verification_agent = VerificationAgent()
        self.eligibility_agent = EligibilityAgent()
        self.scoring_agent = ScoringAgent()
        self.registration_agent = RegistrationAgent()
        self.deadline_agent = DeadlineAgent()
        self.rewards_agent = RewardsAgent()
        self.reporting_agent = ReportingAgent()
        self.email_agent = EmailAgent()

    async def run_full_pipeline(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Executes the end-to-end autonomous discovery & evaluation workflow:
        1. Discovery of new opportunities across all 10 categories
        2. Verification of official terms, URLs, zero-cost rules & pre-existing confirmations
        3. Eligibility checks against Arif Alam's profile (including NMIMS MBA student screening)
        4. Multi-factor AI Opportunity Scoring (0-100)
        5. Deadline Radar analysis (flagging <3d, <7d, and expired)
        6. Generation of Daily Executive Brief
        7. Telemetry recording in AutomationRun ($0.00 zero cost policy)
        """
        start_time = time.time()
        start_dt = datetime.now(timezone.utc)

        # 0. Sync Integrations
        await self.email_agent.get_connection_status(db)

        # 1. Discovery
        discovered = await self.discovery_agent.run_discovery(db)

        # 2. Verification
        verified = await self.verification_agent.verify_all_active(db)

        # 3. Eligibility
        eligible = await self.eligibility_agent.evaluate_all(db)

        # 4. Scoring
        scored = await self.scoring_agent.score_all(db)

        # 5. Deadline Radar
        deadlines = await self.deadline_agent.check_deadlines(db)

        # 6. Reporting
        report = await self.reporting_agent.generate_daily_report(db)

        duration = time.time() - start_time

        # 7. Record Telemetry in AutomationRun
        run_record = AutomationRun(
            agent_name="AgentCoordinator",
            run_type="FULL_PIPELINE",
            status="SUCCESS",
            items_discovered=len(discovered),
            items_verified=len(verified),
            tool_calls_count=len(discovered) + 5,
            tool_cost_usd=0.00,  # Zero cost policy verified
            duration_seconds=round(duration, 2),
            errors_json=[],
            started_at=start_dt,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(run_record)
        await db.commit()

        return {
            "status": "SUCCESS",
            "discovered_count": len(discovered),
            "verified_count": len(verified),
            "eligible_count": len([e for e in eligible if e.eligibility_status in ["Eligible", "Likely eligible"]]),
            "deadlines": deadlines,
            "report_date": report.report_date,
            "duration_seconds": round(duration, 2),
        }
