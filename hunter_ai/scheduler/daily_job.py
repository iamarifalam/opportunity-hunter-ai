"""
Daily Automation Scheduler for Opportunity Hunter AI.
Runs automatically every morning at 8:00 AM IST (Asia/Kolkata)
and supports manual on-demand execution.
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from hunter_ai.config import settings
from hunter_ai.database import AsyncSessionLocal
from hunter_ai.agents.coordinator import AgentCoordinator

scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)
coordinator = AgentCoordinator()


async def execute_daily_automation():
    """Core job that executes the discovery, verification, scoring and reporting cycle."""
    print(f"⏰ [Scheduler] Running Daily Opportunity Automation ({settings.TIMEZONE})...")
    async with AsyncSessionLocal() as session:
        try:
            result = await coordinator.run_full_pipeline(session)
            print(f"✅ [Scheduler] Daily cycle completed: {result}")
        except Exception as e:
            print(f"❌ [Scheduler] Error during daily cycle: {e}")


def start_scheduler():
    """Initializes and starts the background daily scheduler."""
    if not scheduler.running:
        trigger = CronTrigger(
            hour=settings.SCHEDULE_HOUR,
            minute=settings.SCHEDULE_MINUTE,
            timezone=settings.TIMEZONE,
        )
        scheduler.add_job(
            execute_daily_automation,
            trigger=trigger,
            id="daily_opportunity_pipeline",
            replace_existing=True,
            name="Opportunity Hunter Daily Pipeline (8:00 AM IST)",
        )
        scheduler.start()
        print(f"🚀 [Scheduler] Background scheduler started. Next run scheduled at 08:00 AM IST.")


def shutdown_scheduler():
    """Safely shuts down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("🛑 [Scheduler] Background scheduler stopped.")
