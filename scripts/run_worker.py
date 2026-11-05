#!/usr/bin/env python3
"""
Opportunity Hunter AI — Autonomous Persistent Background Worker.
Processes queued tasks from `worker_jobs`, maintains heartbeat in `worker_heartbeats`,
and executes continuous discovery, swag scans, and verification sweeps.
"""

import sys
import os
import asyncio
import signal
import time
from datetime import datetime, timezone, timedelta

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hunter_ai.database import init_db, AsyncSessionLocal
from hunter_ai.agents.orchestrator import OpportunityHunterOrchestrator
from hunter_ai.models import WorkerJob


running = True


def handle_shutdown(signum, frame):
    global running
    print(f"\n[Worker] Received signal {signum}. Initiating graceful worker shutdown...")
    running = False


async def worker_loop():
    global running
    print("=" * 70)
    print("🚀 [Worker] Starting Opportunity Hunter AI Background Worker")
    print(f"⏰ [Worker] Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    # Initialize DB schema
    await init_db()

    orchestrator = OpportunityHunterOrchestrator(worker_id="background-worker-node-1")
    last_heartbeat_time = 0
    last_periodic_cycle_time = time.time()

    # Initial cycle on worker startup
    async with AsyncSessionLocal() as session:
        print("🔍 [Worker] Running initial opportunity discovery & swag scan...")
        await orchestrator.send_heartbeat(session, current_task="Initial Autonomous Cycle")
        cycle_res = await orchestrator.run_full_autonomous_cycle(session)
        print(f"✅ [Worker] Initial cycle completed. Swag synced: {cycle_res.get('swag_synced')}, Discovered: {cycle_res.get('discovered_count')}")

    while running:
        try:
            now = time.time()

            # Heartbeat every 15 seconds
            if now - last_heartbeat_time >= 15:
                async with AsyncSessionLocal() as session:
                    await orchestrator.send_heartbeat(session, current_task="Polling Queue", status="ALIVE")
                last_heartbeat_time = now

            # Fetch and execute next queued job
            async with AsyncSessionLocal() as session:
                job = await orchestrator.fetch_next_job(session)
                if job:
                    print(f"⚡ [Worker] Executing Job #{job.id} ({job.job_type}) - Priority: {job.priority}")
                    exec_res = await orchestrator.execute_job(session, job)
                    print(f"🏁 [Worker] Job #{job.id} finished with status: {exec_res.get('status')}")
                    continue  # Immediately check for next queued job

            # Periodic scheduled cycle (every 6 hours)
            if now - last_periodic_cycle_time >= (6 * 3600):
                print("🔄 [Worker] Triggering 6-hour periodic autonomous pipeline sweep...")
                async with AsyncSessionLocal() as session:
                    await orchestrator.enqueue_job(
                        db=session,
                        job_type="FULL_PIPELINE",
                        priority=7,
                        idempotency_key=f"periodic-{int(now)}",
                    )
                last_periodic_cycle_time = now

            # Idle sleep
            await asyncio.sleep(3)

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"❌ [Worker] Error in worker loop: {e}")
            await asyncio.sleep(5)

    # Final cleanup
    async with AsyncSessionLocal() as session:
        await orchestrator.send_heartbeat(session, current_task="Stopped", status="STOPPED")
    print("🛑 [Worker] Background worker shut down cleanly.")


def main():
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
