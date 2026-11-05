"""
Email Verification Agent for Opportunity Hunter AI.
Handles live Gmail IMAP / OAuth verification of registration receipts and confirmation emails.
Strictly adheres to zero-fabrication: if credentials are not configured, reports NOT_CONFIGURED
and preserves USER_REPORTED status without generating synthetic confirmation tokens.
"""

import os
import email
import imaplib
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.agents.base import BaseAgent
from hunter_ai.models import Integration, Confirmation, Application


class EmailAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="EmailAgent")
        self.imap_server = os.getenv("GMAIL_IMAP_SERVER", "imap.gmail.com")
        self.imap_port = int(os.getenv("GMAIL_IMAP_PORT", "993"))
        self.email_address = os.getenv("GMAIL_USER") or os.getenv("GMAIL_EMAIL")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD") or os.getenv("GMAIL_PASSWORD")

    def is_configured(self) -> bool:
        """Returns True only if valid live email credentials are provided."""
        return bool(self.email_address and self.app_password)

    async def get_connection_status(self, db: AsyncSession) -> Dict[str, Any]:
        """Checks and records integration status in the database."""
        status = "CONNECTED" if self.is_configured() else "NOT_CONFIGURED"
        details = (
            f"Configured for {self.email_address}"
            if self.is_configured()
            else "Gmail credentials not configured in environment. Pre-registered events retain USER_REPORTED_REGISTERED status."
        )

        # Upsert in integrations table
        res = await db.execute(select(Integration).where(Integration.name == "GMAIL"))
        integration = res.scalars().first()
        if not integration:
            integration = Integration(
                name="GMAIL",
                status=status,
                details=details,
                config_preview={"email": self.email_address or "Not set", "imap_server": self.imap_server},
            )
            db.add(integration)
        else:
            integration.status = status
            integration.details = details
            integration.last_checked_at = datetime.now(timezone.utc)

        await db.commit()
        return {
            "name": "Gmail",
            "status": status,
            "configured": self.is_configured(),
            "details": details,
        }

    async def search_confirmation_email(
        self,
        event_name: str,
        organizer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Searches user's inbox for confirmation receipt if credentials exist.
        Never fabricates an email result.
        """
        if not self.is_configured():
            return {
                "status": "NOT_CONFIGURED",
                "verified": False,
                "confirmation_id": None,
                "evidence": f"Gmail IMAP not configured. Event '{event_name}' marked as USER_REPORTED_REGISTERED without fabricated IDs.",
            }

        try:
            # Connect live via IMAP SSL
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.app_password)
            mail.select("inbox")

            search_query = f'(OR SUBJECT "{event_name}" BODY "{event_name}")'
            result, data = mail.search(None, search_query)

            if result == "OK" and data[0]:
                msg_ids = data[0].split()
                latest_id = msg_ids[-1]
                res, msg_data = mail.fetch(latest_id, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject = msg["Subject"]
                from_addr = msg["From"]
                date_str = msg["Date"]
                message_id = msg["Message-ID"] or f"GMAIL-MSG-{latest_id.decode()}"

                mail.close()
                mail.logout()

                return {
                    "status": "AUTHENTICATED",
                    "verified": True,
                    "confirmation_id": message_id.strip("<>"),
                    "subject": subject,
                    "from": from_addr,
                    "date": date_str,
                    "evidence": f"Verified live from inbox: '{subject}' received from {from_addr} on {date_str}.",
                }

            mail.close()
            mail.logout()
            return {
                "status": "NOT_FOUND",
                "verified": False,
                "confirmation_id": None,
                "evidence": f"No email found matching '{event_name}' in inbox.",
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "verified": False,
                "confirmation_id": None,
                "evidence": f"IMAP connection failed: {str(e)}",
            }
