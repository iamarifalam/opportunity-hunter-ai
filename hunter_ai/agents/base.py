"""
Base Agent class for Opportunity Hunter AI.
Provides shared logging, database access, and activity tracking.
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from hunter_ai.models import ActivityLog
from datetime import datetime, timezone


class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    async def log_activity(
        self,
        db: AsyncSession,
        event_type: str,
        title: str,
        details: str = "",
        status: str = "INFO",
        opportunity_id: Optional[int] = None,
    ) -> ActivityLog:
        """Records an auditable event in the persistent activity log."""
        log_entry = ActivityLog(
            event_type=event_type,
            opportunity_id=opportunity_id,
            title=f"[{self.name}] {title}",
            details=details,
            status=status,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        return log_entry
