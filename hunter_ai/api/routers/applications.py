"""
Applications API Router
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.database import get_db
from hunter_ai.models import Application, Opportunity
from hunter_ai.agents.registration_agent import RegistrationAgent

router = APIRouter(prefix="/api/applications", tags=["Applications"])
registration_agent = RegistrationAgent()


class DraftRequest(BaseModel):
    opportunity_id: int
    custom_inputs: Optional[Dict[str, Any]] = None


class SubmitRequest(BaseModel):
    opportunity_id: int
    requires_id_upload: bool = False
    requires_legal_agreement: bool = False


@router.get("")
@router.get("/")
async def list_applications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Application, Opportunity.name.label("opportunity_name"), Opportunity.category.label("category"))
        .join(Opportunity, Application.opportunity_id == Opportunity.id)
        .order_by(Application.updated_at.desc())
    )
    rows = result.all()
    apps = []
    for app, opp_name, cat in rows:
        apps.append({
            "id": app.id,
            "opportunity_id": app.opportunity_id,
            "opportunity_name": opp_name,
            "category": cat,
            "application_status": app.application_status,
            "registration_date": app.registration_date,
            "registration_confirmation": app.registration_confirmation,
            "confirmation_evidence": app.confirmation_evidence,
            "account_used": app.account_used,
            "approval_status": app.approval_status,
            "notes": app.notes,
            "form_draft_data": app.form_draft_data,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
        })
    return apps


@router.post("/draft")
async def create_or_update_draft(req: DraftRequest, db: AsyncSession = Depends(get_db)):
    try:
        app = await registration_agent.prepare_application_draft(
            db=db,
            opportunity_id=req.opportunity_id,
            custom_inputs=req.custom_inputs,
        )
        return {"status": "SUCCESS", "application": app}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/submit")
async def submit_application(req: SubmitRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await registration_agent.submit_application_with_approval_gate(
            db=db,
            opportunity_id=req.opportunity_id,
            requires_id_upload=req.requires_id_upload,
            requires_legal_agreement=req.requires_legal_agreement,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
