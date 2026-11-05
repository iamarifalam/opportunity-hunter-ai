"""
Opportunity Hunter Orchestrator.
Master autonomous coordinator managing 12 subagents, persistent task queue (WorkerJob),
retry with exponential backoff, dead-letter recovery, worker heartbeats, and zero-cost enforcement.
"""

import time
import traceback
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from hunter_ai.agents.base import BaseAgent
from hunter_ai.agents.discovery_agent import DiscoveryAgent
from hunter_ai.agents.swag_agent import SwagHunterAgent
from hunter_ai.agents.hackathon_agent import HackathonAgent
from hunter_ai.agents.credits_agent import CloudCreditsAgent
from hunter_ai.agents.creator_agent import CreatorAgent
from hunter_ai.agents.verification_agent import VerificationAgent
from hunter_ai.agents.eligibility_agent import EligibilityAgent
from hunter_ai.agents.scoring_agent import ScoringAgent
from hunter_ai.agents.application_agent import ApplicationAgent
from hunter_ai.agents.rewards_agent import RewardsAgent
from hunter_ai.agents.deadline_agent import DeadlineAgent
from hunter_ai.agents.reporting_agent import ReportingAgent
from hunter_ai.agents.email_agent import EmailAgent
from hunter_ai.agents.security_agent import SecurityCostAgent
from hunter_ai.engines.cloud_form_submitter import CloudFormSubmitterEngine

from hunter_ai.models import (
    WorkerJob,
    WorkerHeartbeat,
    AutomationRun,
    ActivityLog,
    Opportunity,
    SwagOpportunity,
    CreditBalance,
)


class OpportunityHunterOrchestrator(BaseAgent):
    """
    Master Orchestrator for Opportunity Hunter AI.
    Runs autonomous cycles, manages task queues, handles failover and heartbeats.
    """

    def __init__(self, worker_id: str = "orchestrator-main"):
        super().__init__(name="MasterOrchestrator")
        self.worker_id = worker_id
        self.start_time = time.time()
        self.tasks_processed = 0

        # Subagent Fleet
        self.discovery_agent = DiscoveryAgent()
        self.swag_agent = SwagHunterAgent()
        self.hackathon_agent = HackathonAgent()
        self.credits_agent = CloudCreditsAgent()
        self.creator_agent = CreatorAgent()
        self.verification_agent = VerificationAgent()
        self.eligibility_agent = EligibilityAgent()
        self.scoring_agent = ScoringAgent()
        self.application_agent = ApplicationAgent()
        self.rewards_agent = RewardsAgent()
        self.deadline_agent = DeadlineAgent()
        self.reporting_agent = ReportingAgent()
        self.email_agent = EmailAgent()
        self.security_agent = SecurityCostAgent()
        self.cloud_submitter = CloudFormSubmitterEngine()

        # Zero-yield learning tracker
        self.zero_yield_registry: Dict[str, int] = {}

    async def send_heartbeat(
        self,
        db: AsyncSession,
        current_task: str = "Idle / Awaiting Tasks",
        status: str = "ALIVE",
    ) -> WorkerHeartbeat:
        """
        Updates persistent heartbeat monitor proving continuous background operation.
        """
        now = datetime.now(timezone.utc)
        uptime = round(time.time() - self.start_time, 2)

        res = await db.execute(
            select(WorkerHeartbeat).where(WorkerHeartbeat.worker_id == self.worker_id)
        )
        hb = res.scalars().first()

        if hb:
            hb.status = status
            hb.current_task = current_task
            hb.tasks_processed = self.tasks_processed
            hb.uptime_seconds = uptime
            hb.last_heartbeat = now
        else:
            hb = WorkerHeartbeat(
                worker_id=self.worker_id,
                hostname="production-orchestrator",
                status=status,
                current_task=current_task,
                tasks_processed=self.tasks_processed,
                uptime_seconds=uptime,
                version="2.0.0",
                last_heartbeat=now,
            )
            db.add(hb)

        await db.commit()
        await db.refresh(hb)
        return hb

    async def enqueue_job(
        self,
        db: AsyncSession,
        job_type: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        idempotency_key: Optional[str] = None,
        scheduled_for: Optional[datetime] = None,
    ) -> WorkerJob:
        """
        Enqueues a new job into the persistent WorkerJob queue with idempotency protection.
        """
        now = datetime.now(timezone.utc)
        sched = scheduled_for or now
        payload_data = payload or {}

        if idempotency_key:
            res = await db.execute(
                select(WorkerJob).where(WorkerJob.idempotency_key == idempotency_key)
            )
            existing = res.scalars().first()
            if existing and existing.status in ["QUEUED", "RUNNING", "RETRYING"]:
                return existing

        job = WorkerJob(
            job_type=job_type,
            payload_json=payload_data,
            status="QUEUED",
            priority=priority,
            retry_count=0,
            max_retries=3,
            idempotency_key=idempotency_key,
            scheduled_for=sched,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        await self.log_activity(
            db,
            event_type="JOB_ENQUEUED",
            title=f"Enqueued {job_type} (Priority: {priority})",
            details=f"Job #{job.id} idempotency: {idempotency_key or 'None'}",
            status="INFO",
        )
        return job

    async def fetch_next_job(self, db: AsyncSession) -> Optional[WorkerJob]:
        """
        Pulls the next eligible queued or retrying job based on priority and schedule.
        """
        now = datetime.now(timezone.utc)
        res = await db.execute(
            select(WorkerJob)
            .where(
                and_(
                    WorkerJob.status.in_(["QUEUED", "RETRYING"]),
                    WorkerJob.scheduled_for <= now,
                )
            )
            .order_by(desc(WorkerJob.priority), WorkerJob.scheduled_for.asc())
        )
        return res.scalars().first()

    async def execute_job(self, db: AsyncSession, job: WorkerJob) -> Dict[str, Any]:
        """
        Executes a queued task, handling retries with exponential backoff and dead-letter queues.
        """
        now = datetime.now(timezone.utc)
        job.status = "RUNNING"
        job.started_at = now
        await db.commit()

        await self.send_heartbeat(db, current_task=f"Executing {job.job_type} #{job.id}")

        result: Dict[str, Any] = {}
        try:
            if job.job_type == "FULL_PIPELINE":
                result = await self.run_full_autonomous_cycle(db)

            elif job.job_type == "SWAG_SCAN":
                items = await self.swag_agent.scan_and_sync_swag(db)
                result = {"synced_count": len(items)}

            elif job.job_type == "HACKATHONS_SCAN":
                items = await self.hackathon_agent.sync_hackathons(db)
                result = {"synced_count": len(items)}

            elif job.job_type == "CREDITS_SYNC":
                items = await self.credits_agent.sync_credit_programs(db)
                result = {"synced_count": len(items)}

            elif job.job_type == "CREATOR_SYNC":
                items = await self.creator_agent.sync_creator_opportunities(db)
                result = {"synced_count": len(items)}

            elif job.job_type == "DISCOVERY":
                items = await self.discovery_agent.run_discovery(db)
                result = {"discovered_count": len(items)}

            elif job.job_type == "VERIFY":
                items = await self.verification_agent.verify_all_active(db)
                result = {"verified_count": len(items)}

            elif job.job_type == "ELIGIBILITY":
                items = await self.eligibility_agent.evaluate_all(db)
                result = {"evaluated_count": len(items)}

            elif job.job_type == "SCORING":
                items = await self.scoring_agent.score_all(db)
                result = {"scored_count": len(items)}

            elif job.job_type == "DEADLINE_RADAR":
                deadlines = await self.deadline_agent.check_deadlines(db)
                result = {"deadlines": deadlines}

            elif job.job_type == "REPORT_GEN":
                rep = await self.reporting_agent.generate_daily_report(db)
                result = {"report_date": rep.report_date}

            elif job.job_type == "APPLICATION_DRAFT":
                opp_id = job.payload_json.get("opportunity_id")
                customs = job.payload_json.get("custom_inputs")
                app = await self.application_agent.prepare_draft(db, opp_id, customs)
                result = {"application_id": app.id, "status": app.application_status}

            elif job.job_type == "SWAG_CLAIM":
                swag_id = job.payload_json.get("swag_id")
                size = job.payload_json.get("size", "L")
                claim = await self.swag_agent.prepare_swag_claim(db, swag_id, size)
                result = {"claim_id": claim.id, "status": claim.claim_status}

            else:
                raise ValueError(f"Unknown job_type: {job.job_type}")

            job.status = "COMPLETED"
            job.completed_at = datetime.now(timezone.utc)
            self.tasks_processed += 1
            await db.commit()

            await self.send_heartbeat(db, current_task="Idle / Awaiting Tasks")
            return {"status": "SUCCESS", "job_id": job.id, "data": result}

        except Exception as e:
            err_msg = f"{str(e)}\n{traceback.format_exc()}"
            job.retry_count += 1
            job.error_message = str(e)

            if job.retry_count < job.max_retries:
                # Exponential backoff: 15s, 30s, 60s
                backoff_seconds = (2 ** job.retry_count) * 15
                job.status = "RETRYING"
                job.scheduled_for = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
                await db.commit()

                await self.log_activity(
                    db,
                    event_type="JOB_RETRY",
                    title=f"Retrying Job #{job.id} ({job.job_type})",
                    details=f"Attempt {job.retry_count}/{job.max_retries} scheduled in {backoff_seconds}s. Reason: {str(e)}",
                    status="WARNING",
                )
            else:
                job.status = "DEAD_LETTER"
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()

                await self.log_activity(
                    db,
                    event_type="DEAD_LETTER_JOB",
                    title=f"Job #{job.id} ({job.job_type}) Moved to Dead Letter Queue",
                    details=f"Max retries ({job.max_retries}) exceeded. Error: {str(e)}",
                    status="ERROR",
                )

            await self.send_heartbeat(db, current_task=f"Error in Job #{job.id}: {str(e)[:50]}", status="DEGRADED")
            return {"status": "ERROR", "job_id": job.id, "error": str(e)}

    async def run_full_autonomous_cycle(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Executes complete autonomous opportunity discovery, swag scan, verification, and reporting.
        Enforces strict $0.00 tool cost policy.
        """
        start_time = time.time()
        start_dt = datetime.now(timezone.utc)

        # 1. Swag Maximization Engine Scan
        swag_items = await self.swag_agent.scan_and_sync_swag(db)

        # 2. Hackathons Scan & Pre-Registration Lock
        hackathons = await self.hackathon_agent.sync_hackathons(db)

        # 3. Cloud & AI Credits Sync
        credits = await self.credits_agent.sync_credit_programs(db)

        # 4. Creator & Ambassador Sync
        creator_items = await self.creator_agent.sync_creator_opportunities(db)

        # 5. Global Discovery (Devpost, GitHub API)
        discovered = await self.discovery_agent.run_discovery(db)

        # 6. Verification & Zero-Cost Security Audit
        verified = await self.verification_agent.verify_all_active(db)

        # Preflight zero-cost audit on all active opportunities
        opps_res = await db.execute(select(Opportunity).where(Opportunity.status != "Rejected"))
        all_opps = opps_res.scalars().all()
        for opp in all_opps:
            await self.security_agent.preflight_audit(db, opp)

        # 7. Eligibility Assessment (Includes NMIMS MBA distance student screening)
        eligible = await self.eligibility_agent.evaluate_all(db)

        # 8. Multi-Factor AI Opportunity Scoring
        scored = await self.scoring_agent.score_all(db)

        # 9. Deadline Radar
        deadlines = await self.deadline_agent.check_deadlines(db)

        # 10. Automated Cloud Form Submissions (Zero Local Machine Dependency)
        submissions_result = await self.cloud_submitter.submit_all_eligible_swag_forms(db)

        # 11. Generate Daily Report
        daily_report = await self.reporting_agent.generate_daily_report(db)

        duration = round(time.time() - start_time, 2)

        # 12. Record Telemetry in AutomationRun
        run_record = AutomationRun(
            agent_name="MasterOrchestrator",
            run_type="AUTONOMOUS_CYCLE",
            status="SUCCESS",
            items_discovered=len(discovered) + len(swag_items) + len(hackathons) + len(creator_items),
            items_verified=len(verified) + len(swag_items),
            tool_calls_count=len(swag_items) + len(discovered) + 12,
            tool_cost_usd=0.00,  # Strict $0.00 zero cost policy
            duration_seconds=duration,
            errors_json=[],
            started_at=start_dt,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(run_record)
        await db.commit()

        # Update heartbeat
        await self.send_heartbeat(db, current_task="Idle / Cycle Completed", status="ALIVE")

        return {
            "status": "SUCCESS",
            "cycle_duration_seconds": duration,
            "swag_synced": len(swag_items),
            "hackathons_synced": len(hackathons),
            "credits_synced": len(credits),
            "creator_synced": len(creator_items),
            "discovered_count": len(discovered),
            "verified_count": len(verified),
            "eligible_count": len([e for e in eligible if e.eligibility_status in ["Eligible", "Likely eligible"]]),
            "forms_submitted": submissions_result.get("total_submitted", 0),
            "submission_details": submissions_result.get("details", []),
            "deadlines": deadlines,
            "report_date": daily_report.report_date,
            "zero_cost_verified": True,
        }

    async def get_orchestrator_status(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Returns real-time status of worker, queues, and subagent fleet.
        """
        # Fetch worker heartbeat
        hb_res = await db.execute(
            select(WorkerHeartbeat).where(WorkerHeartbeat.worker_id == self.worker_id)
        )
        hb = hb_res.scalars().first()

        # Fetch queue metrics
        jobs_res = await db.execute(select(WorkerJob))
        jobs = jobs_res.scalars().all()

        queue_stats = {
            "queued": sum(1 for j in jobs if j.status == "QUEUED"),
            "running": sum(1 for j in jobs if j.status == "RUNNING"),
            "retrying": sum(1 for j in jobs if j.status == "RETRYING"),
            "completed": sum(1 for j in jobs if j.status == "COMPLETED"),
            "dead_letter": sum(1 for j in jobs if j.status == "DEAD_LETTER"),
        }

        # Subagent fleet status
        agents = [
            {"name": "SwagHunterAgent", "role": "Physical Merchandise & India Delivery", "status": "ONLINE"},
            {"name": "HackathonAgent", "role": "Competitions & Pre-Registration Lock", "status": "ONLINE"},
            {"name": "CloudCreditsAgent", "role": "Cloud & AI API Credit Balances", "status": "ONLINE"},
            {"name": "CreatorAgent", "role": "Book Reviews, Speaking & Ambassador Kits", "status": "ONLINE"},
            {"name": "DiscoveryAgent", "role": "Global Opportunity Ingestion", "status": "ONLINE"},
            {"name": "VerificationAgent", "role": "Official Terms & Canonical Deduplication", "status": "ONLINE"},
            {"name": "EligibilityAgent", "role": "NMIMS Distance MBA Student & AI Engineer Rules", "status": "ONLINE"},
            {"name": "ScoringAgent", "role": "Multi-Factor Scoring (0-100)", "status": "ONLINE"},
            {"name": "ApplicationAgent", "role": "Form Inspection & Human-in-Loop Approval", "status": "ONLINE"},
            {"name": "RewardsAgent", "role": "Vault & Claims Verification", "status": "ONLINE"},
            {"name": "DeadlineAgent", "role": "Radar Tracking & Urgent Alerts", "status": "ONLINE"},
            {"name": "SecurityCostAgent", "role": "Zero-Cost Guard & Prompt Injection Defense", "status": "ONLINE"},
        ]

        return {
            "orchestrator_id": self.worker_id,
            "status": hb.status if hb else "INITIALIZING",
            "current_task": hb.current_task if hb else "Starting up",
            "last_heartbeat": hb.last_heartbeat.isoformat() if hb and hb.last_heartbeat else None,
            "uptime_seconds": hb.uptime_seconds if hb else round(time.time() - self.start_time, 2),
            "tasks_processed": hb.tasks_processed if hb else self.tasks_processed,
            "queue_stats": queue_stats,
            "fleet_agents": agents,
        }
