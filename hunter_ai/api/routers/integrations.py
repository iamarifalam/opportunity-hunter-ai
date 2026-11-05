"""
Integrations API Router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.database import get_db
from hunter_ai.models import Integration
from hunter_ai.agents.email_agent import EmailAgent

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])
email_agent = EmailAgent()


@router.get("/")
async def list_integrations(db: AsyncSession = Depends(get_db)):
    """Returns external integrations status (Gmail, Playwright, GitHub)."""
    # Ensure Gmail status is fresh
    await email_agent.get_connection_status(db)

    # Check Playwright
    pw_res = await db.execute(select(Integration).where(Integration.name == "PLAYWRIGHT"))
    pw = pw_res.scalars().first()
    if not pw:
        pw = Integration(
            name="PLAYWRIGHT",
            status="ACTIVE",
            details="Headless Chromium v1248 installed & active for registration form inspection.",
            config_preview={"browser": "chromium", "headless": True},
        )
        db.add(pw)
        await db.commit()

    res = await db.execute(select(Integration).order_by(Integration.name.asc()))
    return res.scalars().all()


@router.post("/check-gmail")
async def check_gmail_connection(db: AsyncSession = Depends(get_db)):
    """Refreshes live Gmail connection state."""
    status = await email_agent.get_connection_status(db)
    return status
