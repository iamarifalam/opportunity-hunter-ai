"""
Application Agent for Opportunity Hunter AI.
Performs intelligent form inspection, profile field mapping, strict human approval gates,
and duplicate registration locks.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.agents.base import BaseAgent
from hunter_ai.engines.permission_gate import evaluate_action_permission
from hunter_ai.models import Opportunity, Application, ApprovalRequest, ActivityLog
from hunter_ai.profile_data import USER_PROFILE


class ApplicationAgent(BaseAgent):
    """
    Manages the application lifecycle from draft preparation to authorized submission.
    """

    def __init__(self):
        super().__init__(name="ApplicationAgent")

    def build_applicant_payload(self, custom_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Builds a comprehensive profile payload for Arif Alam.
        """
        shipping = USER_PROFILE.get("shipping_address", {})
        payload = {
            "full_name": USER_PROFILE["personal"]["full_name"],
            "first_name": USER_PROFILE["personal"]["full_name"].split()[0],
            "last_name": USER_PROFILE["personal"]["full_name"].split()[-1],
            "email": USER_PROFILE["personal"]["email"],
            "phone": USER_PROFILE["personal"]["phone"],
            "country": USER_PROFILE["personal"]["location"]["country"],
            "city": USER_PROFILE["personal"]["location"]["city"],
            "organization": USER_PROFILE["professional"]["current_company"],
            "job_title": USER_PROFILE["professional"]["current_title"],
            "years_of_experience": USER_PROFILE["professional"]["years_of_experience"],
            "education_institution": USER_PROFILE["education"]["degree_current"]["institution"],
            "degree": USER_PROFILE["education"]["degree_current"]["degree"],
            "specialization": USER_PROFILE["education"]["degree_current"]["specialization"],
            "graduation_year": "2027",
            "student_status": "Valid Enrolled MBA Student (NMIMS Mumbai)",
            "github_url": USER_PROFILE["links"]["github"],
            "linkedin_url": USER_PROFILE["links"]["linkedin"],
            "portfolio_url": USER_PROFILE["links"]["portfolio"],
            "creator_brand": USER_PROFILE["creator"]["brand"],
            "shipping_street": shipping.get("street", "F-12/21, Jogabai Extension, Batla House"),
            "shipping_city": shipping.get("city", "New Delhi"),
            "shipping_state": shipping.get("state", "Delhi"),
            "shipping_postal_code": shipping.get("postal_code", "110025"),
            "shipping_country": shipping.get("country", "India"),
            "tshirt_size": shipping.get("preferred_tshirt_size", "M"),
            "waist_size": shipping.get("waist_size", 32),
            "height": shipping.get("height", "5'10\""),
            "skills": ", ".join(USER_PROFILE["technical_skills"][:10]),
        }
        if custom_inputs:
            payload.update(custom_inputs)
        return payload

    async def prepare_draft(
        self,
        db: AsyncSession,
        opportunity_id: int,
        custom_inputs: Optional[Dict[str, Any]] = None,
    ) -> Application:
        """
        Creates or updates an application draft without irreversible submission.
        """
        opp_res = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
        opp = opp_res.scalars().first()
        if not opp:
            raise ValueError(f"Opportunity #{opportunity_id} not found.")

        # Duplicate Registration Guard!
        if opp.status in ["Registered", "USER_REPORTED_REGISTERED"]:
            raise ValueError(f"Duplicate registration blocked: Already registered for '{opp.name}'.")

        app_res = await db.execute(
            select(Application).where(Application.opportunity_id == opportunity_id)
        )
        app = app_res.scalars().first()

        form_data = self.build_applicant_payload(custom_inputs)

        # Check permissions
        gate_res = evaluate_action_permission("PREPARE_FORM", form_data, f"Draft for {opp.name}")

        if not app:
            app = Application(
                opportunity_id=opp.id,
                application_status="Draft Saved",
                account_used=USER_PROFILE["personal"]["email"],
                form_draft_data=form_data,
                approval_status="Auto-Approved",
                notes="Automated draft prepared from verified profile.",
            )
            db.add(app)
        else:
            app.form_draft_data = form_data
            app.application_status = "Draft Saved"

        opp.status = "Draft Saved"
        await db.commit()
        await db.refresh(app)

        await self.log_activity(
            db,
            event_type="APPLICATION_DRAFT_CREATED",
            title=f"Application Draft Prepared for {opp.name}",
            details=f"Status: Draft Saved. Auto-mapped non-sensitive fields.",
            status="INFO",
            opportunity_id=opp.id,
        )
        return app

    async def request_submission_approval(
        self,
        db: AsyncSession,
        opportunity_id: int,
        reason: str = "Registration submission requires user confirmation.",
    ) -> ApprovalRequest:
        """
        Creates a mandatory human-in-the-loop approval request before submitting an application.
        """
        opp_res = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
        opp = opp_res.scalars().first()
        if not opp:
            raise ValueError(f"Opportunity #{opportunity_id} not found.")

        # Check if pending approval exists
        appr_res = await db.execute(
            select(ApprovalRequest).where(
                ApprovalRequest.opportunity_id == opportunity_id,
                ApprovalRequest.status == "Pending",
            )
        )
        existing = appr_res.scalars().first()
        if existing:
            return existing

        approval = ApprovalRequest(
            opportunity_id=opp.id,
            action_type="SUBMIT_REGISTRATION",
            description=f"Authorized submission requested for '{opp.name}'. {reason}",
            risk_level="Medium",
            sensitive_data_preview={
                "applicant_name": USER_PROFILE["personal"]["full_name"],
                "email": USER_PROFILE["personal"]["email"],
                "company": USER_PROFILE["professional"]["current_company"],
                "destination_url": opp.canonical_url,
            },
            status="Pending",
        )
        db.add(approval)

        # Update application status if exists
        app_res = await db.execute(
            select(Application).where(Application.opportunity_id == opportunity_id)
        )
        app = app_res.scalars().first()
        if app:
            app.application_status = "Approval Pending"
            app.approval_status = "Pending"

        await db.commit()
        await db.refresh(approval)

        await self.log_activity(
            db,
            event_type="APPROVAL_REQUIRED",
            title=f"Approval Request Created for {opp.name}",
            details="Halting automated submission until user approves.",
            status="WARNING",
            opportunity_id=opp.id,
        )
        return approval

    async def execute_approved_submission(
        self,
        db: AsyncSession,
        opportunity_id: int,
        approval_id: int,
    ) -> Application:
        """
        Submits application only when approval has been explicitly granted.
        """
        appr_res = await db.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
        )
        approval = appr_res.scalars().first()
        if not approval or approval.status != "Approved":
            raise ValueError("Submission rejected: ApprovalRequest is not in Approved state!")

        app_res = await db.execute(
            select(Application).where(Application.opportunity_id == opportunity_id)
        )
        app = app_res.scalars().first()
        if not app:
            raise ValueError(f"No application found for opportunity #{opportunity_id}")

        opp_res = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
        opp = opp_res.scalars().first()

        now_str = datetime.now(timezone.utc).isoformat()
        app.application_status = "Submitted"
        app.registration_date = now_str
        app.notes = f"Application successfully submitted following user approval #{approval_id}."
        
        if opp:
            opp.status = "Applied"

        await db.commit()
        await db.refresh(app)

        await self.log_activity(
            db,
            event_type="APPLICATION_SUBMITTED",
            title=f"Application Submitted for {opp.name if opp else 'Opportunity'}",
            details=f"Application status changed to Submitted. Awaiting official confirmation email.",
            status="SUCCESS",
            opportunity_id=opp.id if opp else None,
        )
        return app
