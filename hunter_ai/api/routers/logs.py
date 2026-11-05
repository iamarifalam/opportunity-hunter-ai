"""
Activity Logs API Router
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.database import get_db
from hunter_ai.models import ActivityLog

router = APIRouter(prefix="/api/logs", tags=["Logs"])


@router.get("/")
async def list_activity_logs(
    event_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(limit)
    if event_type and event_type != "All":
        query = query.where(ActivityLog.event_type == event_type)

    result = await db.execute(query)
    logs = result.scalars().all()
    return logs
