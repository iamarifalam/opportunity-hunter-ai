"""
Database engine and async session management for Opportunity Hunter AI.
Dual engine support:
- SQLite (local development with aiosqlite)
- Managed PostgreSQL (Neon, Supabase, RDS with asyncpg)
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from hunter_ai.config import settings

db_url = settings.get_async_db_url()

if "sqlite" in db_url:
    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL configuration
    engine = create_async_engine(
        db_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables with full constraints and indexes."""
    import hunter_ai.models  # noqa: F401 - Ensure all models are registered in Base.metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
