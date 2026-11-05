"""
Unit test for CloudFormSubmitterEngine.
Tests payload creation, shipping address formatting, and Google Form payload structuring.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from hunter_ai.database import Base
from hunter_ai.engines.cloud_form_submitter import CloudFormSubmitterEngine
from hunter_ai.profile_data import USER_PROFILE


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_cloud_submitter_address_formatting():
    engine = CloudFormSubmitterEngine()
    address = engine._get_applicant_shipping_address()

    assert "Arif Alam" in address
    assert "F-12/21" in address
    assert "Batla House" in address
    assert "New Delhi" in address
    assert "110025" in address
    assert "India" in address


@pytest.mark.asyncio
async def test_cloud_submitter_payload_generation():
    engine = CloudFormSubmitterEngine()
    shipping = USER_PROFILE.get("shipping", {})

    assert shipping.get("postal_code") == "110025"
    assert shipping.get("preferred_tshirt_size") == "M"
    assert shipping.get("waist_size") == 32
