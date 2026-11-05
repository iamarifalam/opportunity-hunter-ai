"""
Profile API Router
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.database import get_db
from hunter_ai.models import UserProfileModel
from hunter_ai.profile_data import USER_PROFILE

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.get("/")
async def get_user_profile(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfileModel).where(UserProfileModel.username == "arif_alam"))
    profile_record = result.scalars().first()

    if profile_record:
        return profile_record.profile_json
    return USER_PROFILE


@router.put("/")
async def update_user_profile(updated_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfileModel).where(UserProfileModel.username == "arif_alam"))
    profile_record = result.scalars().first()

    if not profile_record:
        profile_record = UserProfileModel(username="arif_alam", profile_json=updated_data)
        db.add(profile_record)
    else:
        profile_record.profile_json = updated_data

    await db.commit()
    return {"status": "SUCCESS", "profile": profile_record.profile_json}
