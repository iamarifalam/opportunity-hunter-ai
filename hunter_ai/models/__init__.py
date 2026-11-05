"""
Comprehensive SQLAlchemy relational schema for Opportunity Hunter AI.
Supports evidence-backed discovery, dedicated Swag Maximization Engine,
segregated reward tracking, human-in-the-loop approvals, persistent job queue,
worker heartbeats, and audit telemetry.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from hunter_ai.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Source(Base):
    """Registry of live opportunity sources (APIs, scrapers, feeds)."""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    canonical_url = Column(String(1024), nullable=False)
    category = Column(String(64), nullable=False, index=True)
    health_status = Column(String(32), default="ACTIVE", index=True)  # ACTIVE, DEGRADED, ERROR
    reliability_score = Column(Float, default=1.0)  # 0.0 to 1.0
    last_scraped_at = Column(DateTime, nullable=True)
    error_count = Column(Integer, default=0)
    rate_limit_rpm = Column(Integer, default=30)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    opportunities = relationship("Opportunity", back_populates="source_rel")
    discovery_jobs = relationship("DiscoveryJob", back_populates="source_rel")


class Opportunity(Base):
    """Core opportunity entity with canonical deduplication and verification tracking."""
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(64), nullable=False, index=True)
    # Categories:
    # Swag, Hackathons, Cloud Credits, AI Credits, Cash Rewards, Certifications,
    # Student Benefits, Creator Programs, Events, Research, Gadgets, Bounties, Scholarships
    organization = Column(String(255), nullable=False, index=True)
    official_url = Column(String(1024), nullable=False)
    canonical_url = Column(String(1024), nullable=False, unique=True, index=True)
    country = Column(String(128), default="Global")
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True, index=True)
    source_name = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)
    rules_summary = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Verification: VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, BLOCKED_BY_COST, CLOSED
    verification_status = Column(String(32), default="UNVERIFIED", index=True)

    # Eligibility: Eligible, Likely eligible, Eligibility unclear, Not eligible
    eligibility_status = Column(String(64), default="Eligibility unclear", index=True)
    eligibility_reasons = Column(JSON, default=list)

    # Deadlines (ISO string for quick queries, structured in Deadlines table)
    deadline = Column(String(64), nullable=True)
    registration_deadline = Column(String(64), nullable=True)
    submission_deadline = Column(String(64), nullable=True)

    # Rewards
    reward_value = Column(Float, default=0.0)  # Estimated monetary or credit equivalent
    reward_type = Column(String(128), default="Unknown")  # Cash, Cloud Credits, Swag, etc.
    currency = Column(String(16), default="USD")
    participation_fee = Column(Float, default=0.0)  # Strictly 0.0 for free
    hidden_costs = Column(String(255), default="None detected")

    required_skills = Column(JSON, default=list)
    official_terms_url = Column(String(1024), nullable=True)
    source_evidence = Column(Text, nullable=True)  # Primary excerpt
    last_verified_date = Column(DateTime, default=utc_now)

    # Status: Discovered, Under Verification, Eligible, Approval Required, Ready to Apply,
    # Draft Saved, Submitted, USER_REPORTED_REGISTERED, Registered, Rejected, Closed
    status = Column(String(64), default="Discovered", index=True)
    priority_score = Column(Integer, default=50, index=True)
    score_explanation = Column(JSON, default=dict)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    source_rel = relationship("Source", back_populates="opportunities")
    applications = relationship("Application", back_populates="opportunity", cascade="all, delete-orphan")
    rewards = relationship("Reward", back_populates="opportunity", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="opportunity", cascade="all, delete-orphan")
    evidence_items = relationship("Evidence", back_populates="opportunity", cascade="all, delete-orphan")
    deadlines = relationship("Deadline", back_populates="opportunity", cascade="all, delete-orphan")
    assessments = relationship("EligibilityAssessment", back_populates="opportunity", cascade="all, delete-orphan")


class Evidence(Base):
    """Verbatim text excerpt extracted from official source URL with timestamp and confidence."""
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, index=True)
    evidence_type = Column(String(32), default="GENERAL", index=True)
    # ELIGIBILITY, FEE, DEADLINE, REWARD, TERMS, SWAG_SHIPPING, GENERAL
    verbatim_quote = Column(Text, nullable=False)
    source_url = Column(String(1024), nullable=False)
    confidence_score = Column(Float, default=1.0)
    is_verified = Column(Boolean, default=True)
    extracted_at = Column(DateTime, default=utc_now)

    opportunity = relationship("Opportunity", back_populates="evidence_items")


class EligibilityAssessment(Base):
    """Rule-by-rule matching evidence against Arif Alam's profile."""
    __tablename__ = "eligibility_assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, index=True)
    country_eligible = Column(Boolean, default=True)
    student_eligible = Column(Boolean, default=True)
    professional_eligible = Column(Boolean, default=True)
    skills_matched = Column(JSON, default=list)
    fee_free = Column(Boolean, default=True)
    overall_verdict = Column(String(64), default="Eligible")
    reasoning = Column(JSON, default=dict)
    assessed_at = Column(DateTime, default=utc_now)

    opportunity = relationship("Opportunity", back_populates="assessments")


class Deadline(Base):
    """Structured deadline record with milestone tracking."""
    __tablename__ = "deadlines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, index=True)
    deadline_type = Column(String(32), default="SUBMISSION", index=True)
    # REGISTRATION, SUBMISSION, DRAFT, PRIZE_ANNOUNCEMENT, SWAG_CLAIM
    deadline_timestamp = Column(String(64), nullable=False)
    urgency = Column(String(32), default="NORMAL", index=True)  # NORMAL, APPROACHING_7D, URGENT_3D, EXPIRED
    is_passed = Column(Boolean, default=False)
    verified_via = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    opportunity = relationship("Opportunity", back_populates="deadlines")


class Reward(Base):
    """
    Segregated reward accounting.
    Distinct buckets: CASH, CLOUD_CREDITS, AI_CREDITS, GPU_CREDITS, CERTIFICATION, HARDWARE, SWAG
    Separates POTENTIAL reward vs ACTUALLY CLAIMED / RECEIVED.
    """
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, index=True)
    reward_type = Column(String(128), nullable=False)
    reward_category = Column(String(32), default="OTHER", index=True)
    # CASH, CLOUD_CREDITS, AI_CREDITS, GPU_CREDITS, CERTIFICATION, HARDWARE, SWAG, OTHER
    reward_amount = Column(Float, default=0.0)
    reward_currency = Column(String(16), default="USD")
    reward_description = Column(String(512), nullable=True)
    is_potential = Column(Boolean, default=True)
    reward_received = Column(Boolean, default=False, index=True)
    reward_date = Column(String(64), nullable=True)
    proof_of_receipt = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    opportunity = relationship("Opportunity", back_populates="rewards")


class CreditBalance(Base):
    """Cloud and AI API credit balance tracker with expiry and card requirements."""
    __tablename__ = "credit_balances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider = Column(String(64), nullable=False, index=True)  # AWS, Azure, GCP, NVIDIA, OpenAI, Anthropic, Gemini, Groq
    tier_name = Column(String(128), nullable=False)
    initial_amount = Column(Float, default=0.0)
    remaining_amount = Column(Float, default=0.0)
    currency = Column(String(16), default="USD")
    expiry_date = Column(String(64), nullable=True)
    card_required = Column(Boolean, default=False)
    billing_activated = Column(Boolean, default=False)
    quota_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class SwagOpportunity(Base):
    """
    Dedicated Swag Maximization Engine entity.
    Tracks physical merchandise, free shipping to India verification, and customs safety.
    """
    __tablename__ = "swag_opportunities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    organization = Column(String(255), nullable=False, index=True)
    item_type = Column(String(64), nullable=False, index=True)
    # T-Shirt, Hoodie, Stickers, Backpack, Mug, Bottle, Notebook, Keyboard, Mouse, Dev Kit, Raspberry Pi, Welcome Kit, Hardware
    canonical_url = Column(String(1024), nullable=False, unique=True, index=True)
    official_url = Column(String(1024), nullable=False)
    india_shipping_available = Column(Boolean, default=True, index=True)
    free_shipping = Column(Boolean, default=True, index=True)
    customs_risk = Column(String(32), default="None", index=True)  # None, Low, Medium, High
    stock_status = Column(String(32), default="Available", index=True)  # Available, Limited, Out of Stock, Unknown
    target_audience = Column(String(64), default="Open Source Contributor")  # Student, Working Professional, Creator, Hackathon
    contribution_required = Column(Text, nullable=True)
    swag_score = Column(Integer, default=85, index=True)  # 0-100 Swag Priority Score
    deadline = Column(String(64), nullable=True)
    delivery_timeframe = Column(String(128), default="4-8 weeks")
    verification_status = Column(String(32), default="VERIFIED", index=True)
    source_evidence = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    claims = relationship("SwagClaim", back_populates="swag_rel", cascade="all, delete-orphan")


class SwagClaim(Base):
    """
    Swag claim and physical delivery lifecycle tracking.
    Never marks delivered or shipped without tracking/receipt proof!
    """
    __tablename__ = "swag_claims"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    swag_id = Column(Integer, ForeignKey("swag_opportunities.id"), nullable=False, index=True)
    claim_status = Column(String(64), default="Discovered", index=True)
    # Discovered, Claim Form Prepared, Submitted, Shipped, In Transit, Delivered, Action Required
    selected_size = Column(String(16), default="L")
    shipping_recipient = Column(String(128), default="Arif Alam")
    shipping_address = Column(Text, nullable=True)
    tracking_number = Column(String(128), nullable=True)  # Real tracking only
    courier = Column(String(64), nullable=True)  # DHL, FedEx, India Post, BlueDart
    customs_paid = Column(Float, default=0.0)
    proof_url = Column(String(1024), nullable=True)
    notes = Column(Text, nullable=True)
    claimed_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    swag_rel = relationship("SwagOpportunity", back_populates="claims")


class Application(Base):
    """Application and registration workflow state machine."""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, index=True)
    application_status = Column(String(64), default="Discovered", index=True)
    # Discovered, Drafting, Draft Saved, Approval Pending, Submitted,
    # USER_REPORTED_REGISTERED, Registered, Rejected, Closed
    registration_date = Column(String(64), nullable=True)
    registration_confirmation = Column(String(255), nullable=True)
    confirmation_evidence = Column(Text, nullable=True)
    account_used = Column(String(255), nullable=True)
    documents_required = Column(JSON, default=list)
    approval_status = Column(String(64), default="Auto-Approved", index=True)
    submission_deadline = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    form_draft_data = Column(JSON, default=dict)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    opportunity = relationship("Opportunity", back_populates="applications")
    confirmations = relationship("Confirmation", back_populates="application", cascade="all, delete-orphan")


class Confirmation(Base):
    """Registration confirmation proof (authenticated email or user-reported marker)."""
    __tablename__ = "confirmations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    confirmation_type = Column(String(32), default="USER_REPORTED", index=True)
    # GMAIL_AUTHENTICATED, WEB_SCREENSHOT, USER_REPORTED, MANUAL
    confirmation_identifier = Column(String(255), nullable=True)
    verification_status = Column(String(32), default="USER_REPORTED", index=True)
    # AUTHENTICATED, USER_REPORTED, PENDING_AUTHENTICATION, REJECTED
    raw_evidence = Column(Text, nullable=True)
    received_at = Column(DateTime, default=utc_now)

    application = relationship("Application", back_populates="confirmations")


class ApprovalRequest(Base):
    """Human-in-the-loop security checkpoint for sensitive actions."""
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)
    # UPLOAD_ID, ACCEPT_TERMS, SENSITIVE_INFO, PUBLIC_POST, CREATE_ACCOUNT, SUBMIT_REGISTRATION
    description = Column(Text, nullable=False)
    risk_level = Column(String(32), default="Medium")  # Low, Medium, High, Critical
    sensitive_data_preview = Column(JSON, default=dict)
    status = Column(String(32), default="Pending", index=True)  # Pending, Approved, Rejected
    created_at = Column(DateTime, default=utc_now)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(64), nullable=True)

    opportunity = relationship("Opportunity", back_populates="approval_requests")


class WorkerHeartbeat(Base):
    """Real worker heartbeat monitor proving continuous background operation."""
    __tablename__ = "worker_heartbeats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    worker_id = Column(String(64), unique=True, nullable=False, index=True)
    hostname = Column(String(128), default="local-orchestrator")
    status = Column(String(32), default="ALIVE", index=True)  # ALIVE, DEGRADED, STOPPED
    current_task = Column(String(255), default="Idle / Awaiting Tasks")
    tasks_processed = Column(Integer, default=0)
    uptime_seconds = Column(Float, default=0.0)
    version = Column(String(32), default="1.0.0")
    last_heartbeat = Column(DateTime, default=utc_now, index=True)


class WorkerJob(Base):
    """Persistent task queue for the Opportunity Hunter Orchestrator."""
    __tablename__ = "worker_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_type = Column(String(64), nullable=False, index=True)
    # DISCOVERY, SWAG_SCAN, HACKATHON_SCAN, VERIFY, APPLICATION_PREP, APPLICATION_SUBMIT, GMAIL_POLL, DEADLINE_RADAR, REPORT_GEN
    payload_json = Column(JSON, default=dict)
    status = Column(String(32), default="QUEUED", index=True)
    # QUEUED, RUNNING, COMPLETED, FAILED, RETRYING, DEAD_LETTER
    priority = Column(Integer, default=5, index=True)  # 1 (lowest) to 10 (highest)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    idempotency_key = Column(String(255), unique=True, nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    scheduled_for = Column(DateTime, default=utc_now, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class AutomationRun(Base):
    """Telemetry for agent executions, tool costs ($0.00 zero-cost policy), and run metrics."""
    __tablename__ = "automation_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_name = Column(String(64), nullable=False, index=True)
    run_type = Column(String(64), default="DAILY_JOB", index=True)
    # ORCHESTRATION, DAILY_JOB, ON_DEMAND, DISCOVERY, SWAG_SCAN, VERIFICATION, APPLICATION
    status = Column(String(32), default="SUCCESS", index=True)  # RUNNING, SUCCESS, FAILED
    items_discovered = Column(Integer, default=0)
    items_verified = Column(Integer, default=0)
    tool_calls_count = Column(Integer, default=0)
    tool_cost_usd = Column(Float, default=0.0)  # Zero cost policy verification
    duration_seconds = Column(Float, default=0.0)
    errors_json = Column(JSON, default=list)
    started_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)


class ActivityLog(Base):
    """System activity and audit trail."""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_type = Column(String(64), nullable=False, index=True)
    # Discovery, Swag, Hackathons, Credits, Verification, Eligibility, Scoring, Registration, Approval, Reward, Scheduler, Security, Error
    opportunity_id = Column(Integer, nullable=True, index=True)
    title = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    status = Column(String(32), default="INFO")  # INFO, SUCCESS, WARNING, ERROR
    timestamp = Column(DateTime, default=utc_now, index=True)


# Alias AuditLog to ActivityLog for semantic clarity
AuditLog = ActivityLog


class Integration(Base):
    """External services & connector connection health."""
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True, index=True)
    # GMAIL, PLAYWRIGHT, GITHUB_API, POSTHOG, VERCEL_CRON
    status = Column(String(32), default="NOT_CONFIGURED", index=True)
    # CONNECTED, ACTIVE, NOT_CONFIGURED, ERROR
    last_checked_at = Column(DateTime, default=utc_now)
    details = Column(Text, nullable=True)
    config_preview = Column(JSON, default=dict)


class DiscoveryJob(Base):
    """Execution queue and history of source scrapers and API queries."""
    __tablename__ = "discovery_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True)
    source_name = Column(String(255), nullable=False)
    status = Column(String(32), default="COMPLETED", index=True)  # PENDING, RUNNING, COMPLETED, FAILED
    items_found = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)

    source_rel = relationship("Source", back_populates="discovery_jobs")


class DailyReport(Base):
    """Daily intelligence briefings and summaries."""
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_date = Column(String(32), nullable=False, unique=True, index=True)
    total_discovered = Column(Integer, default=0)
    verified_count = Column(Integer, default=0)
    eligible_count = Column(Integer, default=0)
    swag_count = Column(Integer, default=0)
    approaching_deadlines_count = Column(Integer, default=0)
    potential_reward_total = Column(Float, default=0.0)
    claimed_reward_total = Column(Float, default=0.0)
    categorized_rewards_json = Column(JSON, default=dict)
    highlights_json = Column(JSON, default=list)
    summary_markdown = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)


class Notification(Base):
    """Actionable alerts and notifications for Arif Alam."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(32), default="SYSTEM", index=True)
    # DEADLINE, APPROVAL, REWARD, SWAG, SECURITY, SYSTEM
    severity = Column(String(16), default="INFO")  # INFO, WARNING, CRITICAL, SUCCESS
    is_read = Column(Boolean, default=False, index=True)
    action_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)


class UserProfileModel(Base):
    """Arif Alam's persistent profile document."""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(64), unique=True, default="arif_alam")
    profile_json = Column(JSON, nullable=False)
    shipping_json = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
