"""
API Router for Master Orchestrator and Worker Task Queue.
Endpoints for worker heartbeats, job inspection, job dispatching, and queue management.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from hunter_ai.database import get_db
from hunter_ai.models import WorkerJob, WorkerHeartbeat
from hunter_ai.agents.orchestrator import OpportunityHunterOrchestrator


router = APIRouter(prefix="/api/orchestrator", tags=["Master Orchestrator"])
orchestrator = OpportunityHunterOrchestrator()


class JobEnqueueRequest(BaseModel):
    job_type: str
    payload: Optional[Dict[str, Any]] = None
    priority: int = 5
    idempotency_key: Optional[str] = None


@router.get("/status", response_model=Dict[str, Any])
async def get_orchestrator_status(db: AsyncSession = Depends(get_db)):
    """
    Returns real-time worker heartbeat, queue metrics, and subagent fleet status.
    """
    return await orchestrator.get_orchestrator_status(db)


@router.get("/jobs", response_model=List[Dict[str, Any]])
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    Lists recent tasks in the persistent WorkerJob queue.
    """
    query = select(WorkerJob).order_by(desc(WorkerJob.id)).limit(limit)
    if status:
        query = query.where(WorkerJob.status == status)

    res = await db.execute(query)
    jobs = res.scalars().all()

    return [
        {
            "id": j.id,
            "job_type": j.job_type,
            "status": j.status,
            "priority": j.priority,
            "retry_count": j.retry_count,
            "max_retries": j.max_retries,
            "idempotency_key": j.idempotency_key,
            "error_message": j.error_message,
            "payload": j.payload_json,
            "scheduled_for": j.scheduled_for.isoformat() if j.scheduled_for else None,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        }
        for j in jobs
    ]


@router.post("/jobs", response_model=Dict[str, Any])
async def enqueue_job(
    body: JobEnqueueRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Enqueues a job into the persistent worker queue.
    """
    job = await orchestrator.enqueue_job(
        db=db,
        job_type=body.job_type,
        payload=body.payload,
        priority=body.priority,
        idempotency_key=body.idempotency_key,
    )
    return {
        "status": "QUEUED",
        "job_id": job.id,
        "job_type": job.job_type,
        "priority": job.priority,
        "scheduled_for": job.scheduled_for.isoformat() if job.scheduled_for else None,
    }


@router.post("/jobs/{job_id}/retry", response_model=Dict[str, Any])
async def retry_failed_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Resets a failed or dead-letter job back to QUEUED status.
    """
    res = await db.execute(select(WorkerJob).where(WorkerJob.id == job_id))
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = "QUEUED"
    job.retry_count = 0
    job.error_message = None
    job.scheduled_for = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(job)

    return {"status": "SUCCESS", "job_id": job.id, "message": "Job rescheduled for execution."}


@router.post("/run-cycle", response_model=Dict[str, Any])
async def trigger_cycle_now(db: AsyncSession = Depends(get_db)):
    """
    Directly runs a full autonomous discovery and evaluation cycle.
    """
    result = await orchestrator.run_full_autonomous_cycle(db)
    return result
