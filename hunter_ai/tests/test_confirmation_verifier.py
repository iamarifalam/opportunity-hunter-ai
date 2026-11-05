"""
Tests for Confirmation Verification & Duplicate Registration Prevention
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from hunter_ai.database import Base
from hunter_ai.models import Opportunity, Application
from hunter_ai.agents.verification_agent import VerificationAgent
from hunter_ai.agents.registration_agent import RegistrationAgent


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
async def test_homingo_and_arthaton_verified_with_confirmation_evidence(test_db):
    verifier = VerificationAgent()

    # Create Homingo Hack Days opportunity
    homingo = Opportunity(
        name="Homingo Hack Days Edition 01",
        category="Hackathons",
        organization="Homingo Inc.",
        official_url="https://homingo.dev/hackdays-01",
        canonical_url="https://homingo.dev/hackdays-01",
        country="India, Global",
        reward_value=0.0,
        reward_type="Cash Prize",
        participation_fee=0.0,
        status="Discovered",
    )
    test_db.add(homingo)
    await test_db.commit()
    await test_db.refresh(homingo)

    # Run verification
    verified = await verifier.verify_opportunity(test_db, homingo)

    # In accordance with zero-fabrication rules, must be USER_REPORTED_REGISTERED until live Gmail confirmation
    assert verified.status == "USER_REPORTED_REGISTERED"

    # Check application was created with user-reported evidence and NO fabricated ID
    from sqlalchemy import select
    app_res = await test_db.execute(select(Application).where(Application.opportunity_id == homingo.id))
    app = app_res.scalars().first()
    assert app is not None
    assert app.application_status == "USER_REPORTED_REGISTERED"
    assert app.registration_confirmation is None
    assert "User-reported registration" in app.confirmation_evidence


@pytest.mark.asyncio
async def test_registration_agent_blocks_duplicate_registration(test_db):
    reg_agent = RegistrationAgent()

    # Pre-registered event
    opp = Opportunity(
        name="Arthaton 2026 AI for Finance Hackathon",
        category="Hackathons",
        organization="Arthaton Global",
        official_url="https://arthaton2026.fintech.org",
        canonical_url="https://arthaton2026.fintech.org",
        status="Registered",
    )
    test_db.add(opp)
    await test_db.commit()
    await test_db.refresh(opp)

    # Attempting to draft or register again should raise ValueError
    with pytest.raises(ValueError, match="Duplicate registration blocked"):
        await reg_agent.prepare_application_draft(test_db, opportunity_id=opp.id)
