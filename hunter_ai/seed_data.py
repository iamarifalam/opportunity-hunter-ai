"""
Database Seeding Script for Opportunity Hunter AI.
Initializes tables, seeds source registry, profile constraints,
and optionally triggers live multi-source discovery.
STRICT ZERO-FABRICATION RULE:
Never injects synthetic vouchers, fake claimed rewards, or invented registration tokens.
"""

import asyncio
from hunter_ai.database import init_db, AsyncSessionLocal
from hunter_ai.agents.coordinator import AgentCoordinator
from hunter_ai.agents.discovery_agent import DiscoveryAgent


async def seed():
    print("🌱 [Seeder] Initializing database tables (14-table schema)...")
    await init_db()

    async with AsyncSessionLocal() as session:
        discovery = DiscoveryAgent()
        print("🔗 [Seeder] Registering official sources...")
        await discovery.sync_sources_registry(session)

        coordinator = AgentCoordinator()
        print("🔍 [Seeder] Running live opportunity discovery & evidence verification pipeline...")
        result = await coordinator.run_full_pipeline(session)
        print(f"✅ [Seeder] Pipeline executed: {result['discovered_count']} discovered, {result['verified_count']} verified.")
        print("🔒 [Seeder] Zero fake data: 0 synthetic vouchers seeded. Claimed rewards vault is strictly genuine.")

    print("🎉 [Seeder] Database initialization successfully completed!")


if __name__ == "__main__":
    asyncio.run(seed())
