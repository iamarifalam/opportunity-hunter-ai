"""
API Router for Swag Maximization Engine.
Endpoints for discovering physical developer merchandise, verifying free shipping to India,
and tracking physical delivery claims.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from hunter_ai.database import get_db
from hunter_ai.models import SwagOpportunity, SwagClaim
from hunter_ai.agents.swag_agent import SwagHunterAgent


router = APIRouter(prefix="/api/swag", tags=["Swag Maximization Engine"])
swag_agent = SwagHunterAgent()


class SwagClaimRequest(BaseModel):
    size: str = "L"
    notes: Optional[str] = None


class SwagClaimUpdateRequest(BaseModel):
    status: str
    tracking_number: Optional[str] = None
    courier: Optional[str] = None
    proof_url: Optional[str] = None
    notes: Optional[str] = None


@router.get("", response_model=List[Dict[str, Any]])
async def list_swag_opportunities(
    india_only: bool = Query(False, description="Filter for items with verified free shipping to India"),
    item_type: Optional[str] = Query(None, description="Filter by item type (Hoodie, T-Shirt, Hardware, etc.)"),
    min_score: int = Query(0, ge=0, le=100, description="Minimum Swag Priority Score"),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns verified developer merchandise sorted by Swag Priority Score.
    """
    query = select(SwagOpportunity).order_by(desc(SwagOpportunity.swag_score))

    if india_only:
        query = query.where(
            SwagOpportunity.india_shipping_available == True,
            SwagOpportunity.free_shipping == True,
        )
    if item_type:
        query = query.where(SwagOpportunity.item_type.ilike(f"%{item_type}%"))
    if min_score > 0:
        query = query.where(SwagOpportunity.swag_score >= min_score)

    result = await db.execute(query)
    items = result.scalars().all()

    return [
        {
            "id": item.id,
            "name": item.name,
            "organization": item.organization,
            "item_type": item.item_type,
            "canonical_url": item.canonical_url,
            "official_url": item.official_url,
            "india_shipping_available": item.india_shipping_available,
            "free_shipping": item.free_shipping,
            "customs_risk": item.customs_risk,
            "stock_status": item.stock_status,
            "target_audience": item.target_audience,
            "contribution_required": item.contribution_required,
            "swag_score": item.swag_score,
            "deadline": item.deadline,
            "delivery_timeframe": item.delivery_timeframe,
            "verification_status": item.verification_status,
            "source_evidence": item.source_evidence,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]


@router.post("/scan", response_model=Dict[str, Any])
async def trigger_swag_scan(db: AsyncSession = Depends(get_db)):
    """
    Scans and synchronizes verified physical swag sources.
    """
    synced = await swag_agent.scan_and_sync_swag(db)
    return {
        "status": "SUCCESS",
        "synced_count": len(synced),
        "message": f"Successfully synced {len(synced)} verified physical swag items with India shipping verification.",
    }


@router.get("/metrics", response_model=Dict[str, Any])
async def get_swag_metrics(db: AsyncSession = Depends(get_db)):
    """
    Returns summary statistics for physical swag opportunities and claims.
    """
    return await swag_agent.get_swag_metrics(db)


@router.get("/claims", response_model=List[Dict[str, Any]])
async def list_swag_claims(db: AsyncSession = Depends(get_db)):
    """
    Returns all swag claims and their physical delivery tracking status.
    """
    res = await db.execute(
        select(SwagClaim)
        .options(selectinload(SwagClaim.swag_rel))
        .order_by(desc(SwagClaim.claimed_at))
    )
    claims = res.scalars().all()

    output = []
    for c in claims:
        swag = c.swag_rel
        output.append({
            "id": c.id,
            "swag_id": c.swag_id,
            "swag_name": swag.name if swag else f"Item #{c.swag_id}",
            "organization": swag.organization if swag else "Unknown",
            "item_type": swag.item_type if swag else "Merchandise",
            "claim_status": c.claim_status,
            "selected_size": c.selected_size,
            "shipping_recipient": c.shipping_recipient,
            "shipping_address": c.shipping_address,
            "tracking_number": c.tracking_number,
            "courier": c.courier,
            "customs_paid": c.customs_paid,
            "proof_url": c.proof_url,
            "notes": c.notes,
            "claimed_at": c.claimed_at.isoformat() if c.claimed_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })
    return output


@router.post("/{swag_id}/claim", response_model=Dict[str, Any])
async def prepare_swag_claim(
    swag_id: int,
    body: SwagClaimRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Prepares a physical merchandise claim with Arif Alam's verified Mumbai shipping details.
    """
    try:
        claim = await swag_agent.prepare_swag_claim(db, swag_id, size=body.size, notes=body.notes or "")
        return {
            "status": "SUCCESS",
            "claim_id": claim.id,
            "claim_status": claim.claim_status,
            "selected_size": claim.selected_size,
            "shipping_recipient": claim.shipping_recipient,
            "message": "Swag claim prepared successfully.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/claims/{claim_id}", response_model=Dict[str, Any])
async def update_swag_claim(
    claim_id: int,
    body: SwagClaimUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Updates the delivery lifecycle for a swag claim with tracking and courier confirmation.
    """
    try:
        claim = await swag_agent.update_claim_tracking(
            db=db,
            claim_id=claim_id,
            status=body.status,
            tracking_number=body.tracking_number,
            courier=body.courier,
            proof_url=body.proof_url,
            notes=body.notes,
        )
        return {
            "status": "SUCCESS",
            "claim_id": claim.id,
            "claim_status": claim.claim_status,
            "courier": claim.courier,
            "tracking_number": claim.tracking_number,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
