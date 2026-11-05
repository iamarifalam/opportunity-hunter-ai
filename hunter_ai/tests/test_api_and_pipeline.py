"""
Integration tests for Pipeline, Database persistence, and FastAPI REST endpoints
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from hunter_ai.database import Base, get_db
from hunter_ai.api.app import app
from hunter_ai.agents.coordinator import AgentCoordinator


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
async def test_coordinator_full_pipeline(test_db):
    coordinator = AgentCoordinator()
    result = await coordinator.run_full_pipeline(test_db)

    assert result["status"] == "SUCCESS"
    assert result["discovered_count"] > 10
    assert result["verified_count"] > 10
    assert result["eligible_count"] > 5
    assert "report_date" in result


@pytest.mark.asyncio
async def test_approval_workflow_lifecycle(test_db):
    coordinator = AgentCoordinator()
    await coordinator.run_full_pipeline(test_db)

    from sqlalchemy import select
    from hunter_ai.models import Opportunity
    opp_res = await test_db.execute(select(Opportunity).where(Opportunity.status.notin_(["Registered", "USER_REPORTED_REGISTERED"])))
    opp = opp_res.scalars().first()
    assert opp is not None

    # Submit application simulating document upload requirement (should trigger approval)
    reg_agent = coordinator.registration_agent
    res = await reg_agent.submit_application_with_approval_gate(
        db=test_db,
        opportunity_id=opp.id,
        requires_id_upload=True,
    )

    assert res["status"] == "APPROVAL_REQUIRED"
    assert "approval_id" in res

    # Verify opportunity is marked 'Approval Required'
    await test_db.refresh(opp)
    assert opp.status == "Approval Required"


@pytest.mark.asyncio
async def test_api_endpoints_health_and_opportunities(test_db):
    app.dependency_overrides[get_db] = lambda: test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        health_resp = await ac.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "HEALTHY"
        assert health_resp.json()["user"] == "Arif Alam"

        profile_resp = await ac.get("/api/profile/")
        assert profile_resp.status_code == 200
        assert profile_resp.json()["personal"]["full_name"] == "Arif Alam"

        metrics_resp = await ac.get("/api/rewards/metrics")
        assert metrics_resp.status_code == 200
        assert "total_potential_usd" in metrics_resp.json()
    app.dependency_overrides.clear()

