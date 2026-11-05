"""
Approval Requests API Router (Human-in-the-Loop Security Gate)
"""

from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.database import get_db
from hunter_ai.models import ApprovalRequest, Opportunity, Application, ActivityLog

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])


class ApprovalActionRequest(BaseModel):
    action: str  # "APPROVE" or "REJECT"
    notes: Optional[str] = None


@router.get("")
@router.get("/")
async def list_approvals(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = (
        select(ApprovalRequest, Opportunity.name.label("opportunity_name"))
        .join(Opportunity, ApprovalRequest.opportunity_id == Opportunity.id)
        .order_by(ApprovalRequest.created_at.desc())
    )
    if status and status != "All":
        query = query.where(ApprovalRequest.status == status)

    result = await db.execute(query)
    rows = result.all()
    
    approvals = []
    for req, opp_name in rows:
        approvals.append({
            "id": req.id,
            "opportunity_id": req.opportunity_id,
            "opportunity_name": opp_name,
            "action_type": req.action_type,
            "description": req.description,
            "risk_level": req.risk_level,
            "sensitive_data_preview": req.sensitive_data_preview,
            "status": req.status,
            "created_at": req.created_at,
            "resolved_at": req.resolved_at,
            "resolved_by": req.resolved_by,
        })
    return approvals


@router.post("/{approval_id}/action")
async def resolve_approval(
    approval_id: int,
    action_req: ApprovalActionRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ApprovalRequest).where(ApprovalRequest.id == approval_id))
    req = result.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if req.status != "Pending":
        raise HTTPException(status_code=400, detail=f"Request already resolved ({req.status})")

    # Fetch opportunity and application
    opp_res = await db.execute(select(Opportunity).where(Opportunity.id == req.opportunity_id))
    opp = opp_res.scalars().first()

    app_res = await db.execute(select(Application).where(Application.opportunity_id == req.opportunity_id))
    app = app_res.scalars().first()

    now = datetime.now(timezone.utc)
    req.resolved_at = now
    req.resolved_by = "Arif Alam (Explicit Approval)"

    if action_req.action.upper() == "APPROVE":
        req.status = "Approved"
        if opp:
            opp.status = "Submitted"
        if app:
            app.approval_status = "Approved"
            app.application_status = "Submitted"
            app.registration_date = now.strftime("%Y-%m-%d %H:%M:%S UTC")
            app.registration_confirmation = f"USER-APPROVED-APP-{req.id}"
            app.notes = action_req.notes or "Explicitly authorized by Arif Alam."

        log_status = "SUCCESS"
        log_title = f"Action Approved by User: {req.action_type} for {opp.name if opp else 'Event'}"
    else:
        req.status = "Rejected"
        if opp:
            opp.status = "Rejected"
        if app:
            app.approval_status = "Rejected"
            app.application_status = "Rejected"
            app.notes = action_req.notes or "Declined by Arif Alam."

        log_status = "WARNING"
        log_title = f"Action Rejected by User: {req.action_type} for {opp.name if opp else 'Event'}"

    log = ActivityLog(
        event_type="Approval",
        opportunity_id=req.opportunity_id,
        title=log_title,
        details=f"Decision: {req.status}. Reason: {action_req.notes or 'No additional notes'}",
        status=log_status,
        timestamp=now,
    )
    db.add(log)
    await db.commit()

    return {"status": "SUCCESS", "decision": req.status, "approval_id": req.id}
