"""
Opportunity Hunter AI Configuration Settings
Supports SQLite (local development) and Managed PostgreSQL (Neon, Supabase, AWS RDS).
"""

import os
from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "Opportunity Hunter AI"
    APP_ENV: str = "development"  # development, staging, production
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # Database
    # On Vercel serverless, /var/task is read-only; default to /tmp/hunter_ai.db if SQLite
    DATABASE_PATH: Path = (
        Path("/tmp/hunter_ai.db")
        if (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
        else (BASE_DIR / "hunter_ai.db")
    )
    # Overridable via DATABASE_URL env var (e.g. postgresql+asyncpg://... or postgres://...)
    DATABASE_URL: str = ""
    SYNC_DATABASE_URL: str = ""

    # Vercel & Worker Deployment
    VERCEL: bool = False
    VERCEL_ENV: str = "development"
    CRON_SECRET: str = "opportunity-hunter-cron-secret-dev"

    # Automation & Scheduler
    SCHEDULE_HOUR: int = 8       # 8:00 AM IST
    SCHEDULE_MINUTE: int = 0
    TIMEZONE: str = "Asia/Kolkata"
    HEADLESS_BROWSER: bool = True
    WORKER_HEARTBEAT_INTERVAL: int = 30  # seconds

    # Security & FinOps Policies
    STRICT_ZERO_COST: bool = True
    AUTO_APPROVE_NON_SENSITIVE: bool = True
    MAX_TOOL_COST_LIMIT_USD: float = 0.00  # Strict zero cost

    # Email Intelligence (Optional credentials, never fabricated)
    GMAIL_IMAP_SERVER: str = "imap.gmail.com"
    GMAIL_IMAP_PORT: int = 993
    GMAIL_USER: str = ""
    GMAIL_APP_PASSWORD: str = ""

    # Analytics
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://app.posthog.com"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    @model_validator(mode="after")
    def adjust_for_serverless(self) -> "Settings":
        is_serverless = bool(
            os.getenv("VERCEL")
            or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
            or self.VERCEL
            or os.getenv("VERCEL_ENV")
        )
        if is_serverless:
            self.VERCEL = True
            if not self.DATABASE_URL:
                self.DATABASE_PATH = Path("/tmp/hunter_ai.db")
        return self

    def get_async_db_url(self) -> str:
        """Normalizes DATABASE_URL for async SQLAlchemy drivers."""
        url = self.DATABASE_URL
        if not url:
            return f"sqlite+aiosqlite:///{self.DATABASE_PATH}"
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("sqlite:///") and not url.startswith("sqlite+aiosqlite:///"):
            url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return url


settings = Settings()
