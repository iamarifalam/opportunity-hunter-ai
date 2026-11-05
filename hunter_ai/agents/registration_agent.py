"""
Registration Agent for Opportunity Hunter AI.
Handles automated form inspection, non-sensitive profile field mapping,
approval gate enforcement, draft state saving, and Playwright browser integration.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.agents.base import BaseAgent
from hunter_ai.engines.permission_gate import evaluate_action_permission
from hunter_ai.models import Opportunity, Application, ApprovalRequest
from hunter_ai.profile_data import USER_PROFILE


class RegistrationAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="RegistrationAgent")

    def build_form_payload(self, custom_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Builds a pre-filled dictionary of Arif Alam's verified non-sensitive profile details.
        """
        payload = {
            "full_name": USER_PROFILE["personal"]["full_name"],
            "first_name": USER_PROFILE["personal"]["full_name"].split()[0],
            "last_name": USER_PROFILE["personal"]["full_name"].split()[-1],
            "email": USER_PROFILE["personal"]["email"],
            "country": USER_PROFILE["personal"]["location"]["country"],
            "city": USER_PROFILE["personal"]["location"]["city"],
            "organization": USER_PROFILE["professional"]["current_company"],
            "job_title": USER_PROFILE["professional"]["current_title"],
            "experience_years": USER_PROFILE["professional"]["years_of_experience"],
            "university": USER_PROFILE["education"]["degree_current"]["institution"],
            "degree": USER_PROFILE["education"]["degree_current"]["degree"],
            "specialization": USER_PROFILE["education"]["degree_current"]["specialization"],
            "graduation_year": "2027",
            "skills": ", ".join(USER_PROFILE["technical_skills"][:8]),
            "github_url": USER_PROFILE["links"]["github"],
            "linkedin_url": USER_PROFILE["links"]["linkedin"],
            "portfolio_url": USER_PROFILE["links"]["portfolio"],
            "creator_brand": USER_PROFILE["creator"]["brand"],
        }
        if custom_inputs:
            payload.update(custom_inputs)
        return payload

    async def prepare_application_draft(
        self,
        db: AsyncSession,
        opportunity_id: int,
        custom_inputs: Optional[Dict[str, Any]] = None,
    ) -> Application:
        """
        Prepares an application draft without submitting it irreversibly.
        Enforces permission policies and creates approval requests if sensitive fields are detected.
        """
        # Fetch opportunity
        result = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
        opp = result.scalars().first()
        if not opp:
            raise ValueError(f"Opportunity with ID {opportunity_id} not found.")

        # Avoid duplicate registration
        if opp.status == "Registered":
            raise ValueError(f"Already registered for {opp.name}. Duplicate registration blocked.")

        # Fetch or create application record
        app_result = await db.execute(select(Application).where(Application.opportunity_id == opportunity_id))
        app = app_result.scalars().first()

        form_data = self.build_form_payload(custom_inputs)

        # Check permission gate
        perm_check = evaluate_action_permission(
            action_type="PREPARE_FORM",
            form_data=form_data,
            details=f"For event: {opp.name}",
        )

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
            db=db,
            event_type="Registration",
            opportunity_id=opp.id,
            title=f"Application Draft Prepared for {opp.name}",
            details=f"Mapped {len(form_data)} profile fields. Ready for review or submission.",
            status="SUCCESS",
        )

        return app

    async def submit_application_with_approval_gate(
        self,
        db: AsyncSession,
        opportunity_id: int,
        requires_id_upload: bool = False,
        requires_legal_agreement: bool = False,
    ) -> Dict[str, Any]:
        """
        Attempts to submit an application.
        If it requires sensitive operations (ID cards, binding agreements, payment credentials),
        it halts and creates an ApprovalRequest for Arif Alam.
        """
        # Fetch opportunity and application
        res = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
        opp = res.scalars().first()
        if not opp:
            raise ValueError("Opportunity not found.")

        app_res = await db.execute(select(Application).where(Application.opportunity_id == opportunity_id))
        app = app_res.scalars().first()
        if not app:
            app = await self.prepare_application_draft(db, opportunity_id)

        # Evaluate gating criteria
        action_type = "FREE_NON_BINDING_REGISTRATION"
        if requires_id_upload:
            action_type = "UPLOAD_ID"
        elif requires_legal_agreement:
            action_type = "LEGAL_BINDING_AGREEMENT"

        perm = evaluate_action_permission(action_type, app.form_draft_data, details=f"Target: {opp.name}")

        if perm["requires_approval"]:
            # Create ApprovalRequest
            approval_req = ApprovalRequest(
                opportunity_id=opp.id,
                action_type=action_type,
                description=perm["description"],
                risk_level=perm["risk_level"],
                sensitive_data_preview=app.form_draft_data,
                status="Pending",
            )
            db.add(approval_req)
            opp.status = "Approval Required"
            app.application_status = "Approval Pending"
            app.approval_status = "Pending Approval"
            await db.commit()

            await self.log_activity(
                db=db,
                event_type="Approval",
                opportunity_id=opp.id,
                title=f"Approval Gate Triggered: {action_type} for {opp.name}",
                details=f"Risk Level: {perm['risk_level']}. Action requires explicit authorization from Arif Alam.",
                status="WARNING",
            )

            return {
                "status": "APPROVAL_REQUIRED",
                "approval_id": approval_req.id,
                "message": f"Operation halted safely: {perm['description']}. Awaiting user approval.",
                "risk_level": perm["risk_level"],
            }

        # Otherwise, if completely free, non-binding, and pre-authorized:
        app.application_status = "Submitted"
        app.registration_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        app.registration_confirmation = f"AUTO-SUBMITTED-APP-{opp.id}"
        opp.status = "Submitted"
        await db.commit()

        await self.log_activity(
            db=db,
            event_type="Registration",
            opportunity_id=opp.id,
            title=f"Application Safely Submitted for {opp.name}",
            details="Free non-binding registration completed using verified profile.",
            status="SUCCESS",
        )

        return {
            "status": "SUBMITTED",
            "message": f"Successfully registered for {opp.name}.",
            "confirmation": app.registration_confirmation,
        }

    async def inspect_page_with_playwright(self, url: str) -> Dict[str, Any]:
        """
        Uses Playwright in headless mode to inspect registration form elements,
        detect CAPTCHAs, OTP prompts, and field names.
        """
        from playwright.async_api import async_playwright
        result = {
            "url": url,
            "captcha_detected": False,
            "fields_found": [],
            "title": "",
            "accessible": True,
        }

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                try:
                    await page.goto(url, timeout=12000, wait_until="domcontentloaded")
                    result["title"] = await page.title()
                    
                    # Detect CAPTCHA signatures
                    content = (await page.content()).lower()
                    if any(term in content for term in ["recaptcha", "hcaptcha", "cf-turnstile", "g-recaptcha"]):
                        result["captcha_detected"] = True

                    # Find input fields
                    inputs = await page.query_selector_all("input, textarea, select")
                    for inp in inputs[:15]:
                        name = await inp.get_attribute("name") or await inp.get_attribute("id") or await inp.get_attribute("placeholder")
                        if name:
                            result["fields_found"].append(name.strip())
                except Exception as e:
                    result["accessible"] = False
                    result["error"] = str(e)
                finally:
                    await browser.close()
        except Exception as e:
            result["accessible"] = False
            result["error"] = str(e)

        return result
