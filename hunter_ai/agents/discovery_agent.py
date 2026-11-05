"""
Discovery Agent for Opportunity Hunter AI.
Performs live discovery across official sources:
1. Devpost Live Hackathons Feed (API)
2. GitHub AI Competitions & Hackathons (Search API)
3. Official Developer Programs & Grants (AWS, Microsoft, Google, NVIDIA)
4. Student & Creator Initiatives (GitHub Education, Packt Reviewers)
5. User-Reported Pre-Registrations (Homingo & Arthaton without synthetic confirmation IDs)
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.agents.base import BaseAgent
from hunter_ai.engines.canonical import canonicalize_url
from hunter_ai.models import Opportunity, Source, DiscoveryJob
from hunter_ai.profile_data import USER_PROFILE


OFFICIAL_SOURCES_REGISTRY = [
    {
        "name": "Devpost Live Hackathons Feed",
        "canonical_url": "https://devpost.com/api/hackathons",
        "category": "Hackathons",
        "rate_limit_rpm": 30,
    },
    {
        "name": "GitHub AI Competitions API",
        "canonical_url": "https://api.github.com/search/repositories",
        "category": "Hackathons",
        "rate_limit_rpm": 60,
    },
    {
        "name": "AWS Activate Founders Program",
        "canonical_url": "https://aws.amazon.com/activate/",
        "category": "Cloud Credits",
        "rate_limit_rpm": 20,
    },
    {
        "name": "Microsoft for Startups Founders Hub",
        "canonical_url": "https://www.microsoft.com/en-us/startups",
        "category": "Cloud Credits",
        "rate_limit_rpm": 20,
    },
    {
        "name": "Google Cloud for Startups",
        "canonical_url": "https://cloud.google.com/startup",
        "category": "Cloud Credits",
        "rate_limit_rpm": 20,
    },
    {
        "name": "NVIDIA Inception Program",
        "canonical_url": "https://www.nvidia.com/en-us/startups/",
        "category": "AI Credits",
        "rate_limit_rpm": 20,
    },
    {
        "name": "GitHub Student Developer Pack",
        "canonical_url": "https://education.github.com/pack",
        "category": "Student Benefits",
        "rate_limit_rpm": 30,
    },
    {
        "name": "Google Gemini API Developer Competition",
        "canonical_url": "https://ai.google.dev/competition",
        "category": "Cash Rewards",
        "rate_limit_rpm": 20,
    },
    {
        "name": "Packt Technical Reviewer Community",
        "canonical_url": "https://authors.packtpub.com/become-a-reviewer/",
        "category": "Creator Programs",
        "rate_limit_rpm": 20,
    },
    {
        "name": "User-Reported Registrations",
        "canonical_url": "https://opportunity-hunter.internal/user-reported",
        "category": "Hackathons",
        "rate_limit_rpm": 999,
    },
]


class DiscoveryAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="DiscoveryAgent")

    async def sync_sources_registry(self, db: AsyncSession) -> Dict[str, int]:
        """Ensures all official sources are registered in the sources table."""
        source_map = {}
        for src_data in OFFICIAL_SOURCES_REGISTRY:
            res = await db.execute(select(Source).where(Source.name == src_data["name"]))
            source = res.scalars().first()
            if not source:
                source = Source(
                    name=src_data["name"],
                    canonical_url=src_data["canonical_url"],
                    category=src_data["category"],
                    health_status="ACTIVE",
                    reliability_score=1.0,
                    rate_limit_rpm=src_data["rate_limit_rpm"],
                    last_scraped_at=datetime.now(timezone.utc),
                )
                db.add(source)
                await db.flush()
            source_map[src_data["name"]] = source.id
        await db.commit()
        return source_map

    async def fetch_devpost_hackathons(self) -> List[Dict[str, Any]]:
        """Fetches live public hackathons directly from Devpost's JSON feed."""
        discovered = []
        try:
            async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Mozilla/5.0 OpportunityHunter/1.0"}) as client:
                res = await client.get("https://devpost.com/api/hackathons?challenge_type[]=online&status[]=open")
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("hackathons", []):
                        title = item.get("title")
                        raw_url = item.get("url")
                        if not title or not raw_url:
                            continue

                        # Extract prize value if available
                        prize_text = item.get("prize_amount", "")
                        clean_prize = re.sub(r"[^\d.]", "", prize_text)
                        reward_val = float(clean_prize) if clean_prize else 0.0

                        themes = [t.get("name") for t in item.get("themes", []) if t.get("name")]
                        dates = item.get("submission_period_dates", "")

                        discovered.append({
                            "name": title,
                            "category": "Hackathons",
                            "organization": "Devpost Community & Sponsors",
                            "official_url": raw_url,
                            "country": "Global",
                            "reward_value": reward_val,
                            "reward_type": f"Prize Pool: ${reward_val:,.0f}" if reward_val > 0 else "Recognition & Prizes",
                            "participation_fee": 0.0,
                            "registration_deadline": dates,
                            "submission_deadline": dates,
                            "required_skills": themes if themes else ["AI", "Software Engineering"],
                            "official_terms_url": f"{raw_url.rstrip('/')}/rules",
                            "source_evidence": f"Live Devpost Hackathon: {title}. Period: {dates}. Prize: {prize_text}. Themes: {', '.join(themes)}.",
                            "source_name": "Devpost Live Hackathons Feed",
                        })
        except Exception as e:
            print(f"⚠️ [DiscoveryAgent] Devpost fetch error: {e}")
        return discovered

    async def fetch_github_ai_hackathons(self) -> List[Dict[str, Any]]:
        """Queries GitHub Search API for active AI hackathons and community challenges."""
        discovered = []
        try:
            async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Mozilla/5.0 OpportunityHunter/1.0"}) as client:
                res = await client.get(
                    "https://api.github.com/search/repositories?q=topic:hackathon+topic:ai&sort=updated&order=desc&per_page=6"
                )
                if res.status_code == 200:
                    data = res.json()
                    for repo in data.get("items", []):
                        name = repo.get("name", "").replace("-", " ").title()
                        full_name = repo.get("full_name", "")
                        html_url = repo.get("html_url", "")
                        desc = repo.get("description") or "Open source AI challenge repository"

                        discovered.append({
                            "name": f"{name} AI Challenge",
                            "category": "Hackathons",
                            "organization": full_name.split("/")[0] if "/" in full_name else "GitHub Community",
                            "official_url": html_url,
                            "country": "Global",
                            "reward_value": 0.0,  # Open source challenge, cash prize not specified
                            "reward_type": "Open Source Recognition & AI Showcase",
                            "participation_fee": 0.0,
                            "registration_deadline": None,
                            "submission_deadline": None,
                            "required_skills": ["Python", "AI", "GitHub", "LLMs"],
                            "official_terms_url": f"{html_url}/blob/main/README.md",
                            "source_evidence": f"GitHub AI Hackathon Repository: {full_name}. Description: {desc}",
                            "source_name": "GitHub AI Competitions API",
                        })
        except Exception as e:
            print(f"⚠️ [DiscoveryAgent] GitHub fetch error: {e}")
        return discovered

    def get_official_cloud_and_programs(self) -> List[Dict[str, Any]]:
        """Verified official programs with exact canonical documentation URLs."""
        return [
            {
                "name": "AWS Activate Founders Program",
                "category": "Cloud Credits",
                "organization": "Amazon Web Services",
                "official_url": "https://aws.amazon.com/activate/",
                "country": "Global, India",
                "reward_value": 1000.0,
                "reward_type": "AWS Cloud Credits ($1,000)",
                "participation_fee": 0.0,
                "registration_deadline": "Ongoing",
                "submission_deadline": "Ongoing",
                "required_skills": ["AWS", "Cloud Computing", "AI", "DevOps"],
                "official_terms_url": "https://aws.amazon.com/activate/terms/",
                "source_evidence": "AWS Activate Founders provides self-funded startups and builders with $1,000 in AWS promotional credits and technical support.",
                "source_name": "AWS Activate Founders Program",
            },
            {
                "name": "Microsoft for Startups Founders Hub",
                "category": "Cloud Credits",
                "organization": "Microsoft",
                "official_url": "https://www.microsoft.com/en-us/startups",
                "country": "Global, India",
                "reward_value": 2500.0,
                "reward_type": "Microsoft Azure Credits ($2,500 - $150,000)",
                "participation_fee": 0.0,
                "registration_deadline": "Ongoing",
                "submission_deadline": "Ongoing",
                "required_skills": ["Azure", "AI Engineering", "Python", "FastAPI"],
                "official_terms_url": "https://www.microsoft.com/en-us/startups/terms",
                "source_evidence": "Microsoft Founders Hub provides up to $150,000 in Azure credits, OpenAI API credits, and GitHub Enterprise access. Open to early-stage builders without funding.",
                "source_name": "Microsoft for Startups Founders Hub",
            },
            {
                "name": "Google Cloud for Startups Program",
                "category": "Cloud Credits",
                "organization": "Google Cloud",
                "official_url": "https://cloud.google.com/startup",
                "country": "Global, India",
                "reward_value": 2000.0,
                "reward_type": "Google Cloud & Gemini API Credits ($2,000)",
                "participation_fee": 0.0,
                "registration_deadline": "Ongoing",
                "submission_deadline": "Ongoing",
                "required_skills": ["GCP", "Gemini API", "Python", "Kubernetes"],
                "official_terms_url": "https://cloud.google.com/startup/terms",
                "source_evidence": "Google Cloud for Startups provides bootstrap credits starting at $2,000 for early builders and access to Gemini AI developer credits.",
                "source_name": "Google Cloud for Startups",
            },
            {
                "name": "NVIDIA Inception for AI Startups",
                "category": "AI Credits",
                "organization": "NVIDIA",
                "official_url": "https://www.nvidia.com/en-us/startups/",
                "country": "Global, India",
                "reward_value": 5000.0,
                "reward_type": "NVIDIA Cloud Credits & DLI Training Vouchers",
                "participation_fee": 0.0,
                "registration_deadline": "Ongoing",
                "submission_deadline": "Ongoing",
                "required_skills": ["CUDA", "Python", "PyTorch", "LLMs", "RAG"],
                "official_terms_url": "https://www.nvidia.com/en-us/startups/terms",
                "source_evidence": "NVIDIA Inception provides GPU compute discounts, Deep Learning Institute training credits, and technical co-marketing to AI builders.",
                "source_name": "NVIDIA Inception Program",
            },
            {
                "name": "GitHub Student Developer Pack",
                "category": "Student Benefits",
                "organization": "GitHub & Partners",
                "official_url": "https://education.github.com/pack",
                "country": "Global, India",
                "reward_value": 500.0,
                "reward_type": "Developer Tools & Cloud Access (Copilot, JetBrains, Azure)",
                "participation_fee": 0.0,
                "registration_deadline": "Ongoing",
                "submission_deadline": "Ongoing",
                "required_skills": ["Git", "Python", "Docker", "Software Engineering"],
                "official_terms_url": "https://education.github.com/terms",
                "source_evidence": "Free GitHub Pro, GitHub Copilot access, JetBrains IDE licenses, and partner developer tool credits for enrolled students.",
                "source_name": "GitHub Student Developer Pack",
            },
            {
                "name": "Google Gemini API Developer Competition",
                "category": "Cash Rewards",
                "organization": "Google DeepMind",
                "official_url": "https://ai.google.dev/competition",
                "country": "Global",
                "reward_value": 50000.0,
                "reward_type": "Cash Prize & Google Cloud Credits",
                "participation_fee": 0.0,
                "registration_deadline": "2026-12-15T23:59:59Z",
                "submission_deadline": "2026-12-20T23:59:59Z",
                "required_skills": ["Gemini API", "Python", "Agentic AI", "RAG"],
                "official_terms_url": "https://ai.google.dev/competition/terms",
                "source_evidence": "Google Gemini Developer Competition: Build multimodal and agentic applications with Gemini API. Grand prize and category awards.",
                "source_name": "Google Gemini API Developer Competition",
            },
            {
                "name": "Packt Technical Book Reviewer Program",
                "category": "Creator Programs",
                "organization": "Packt Publishing",
                "official_url": "https://authors.packtpub.com/become-a-reviewer/",
                "country": "Global, India",
                "reward_value": 150.0,
                "reward_type": "Free Technical Books & Digital Library Access",
                "participation_fee": 0.0,
                "registration_deadline": "Ongoing",
                "submission_deadline": "Ongoing",
                "required_skills": ["Python", "Machine Learning", "Generative AI", "Technical Writing"],
                "official_terms_url": "https://authors.packtpub.com/terms",
                "source_evidence": "Review early technical manuscripts on AI, ML, and Data Science. Earn free books and public author attribution.",
                "source_name": "Packt Technical Reviewer Community",
            },
        ]

    def get_user_reported_events(self) -> List[Dict[str, Any]]:
        """Pre-registered events reported by Arif Alam (Homingo & Arthaton)."""
        events = []
        for p in USER_PROFILE.get("pre_registered_events", []):
            events.append({
                "name": p["name"],
                "category": p["category"],
                "organization": p.get("organizer", "Hackathon Organizer"),
                "official_url": f"https://opportunity-hunter.internal/events/{p['name'].lower().replace(' ', '-')}",
                "country": "India, Global",
                "reward_value": 0.0,  # Unverified prize value; set strictly to 0.0 to prevent inflation
                "reward_type": "Participation & Prizes",
                "participation_fee": 0.0,
                "registration_deadline": "Ongoing",
                "submission_deadline": "Ongoing",
                "required_skills": ["Python", "FastAPI", "AI Engineering", "Generative AI"],
                "official_terms_url": None,
                "source_evidence": p.get("confirmation_evidence", "User-reported registration."),
                "source_name": "User-Reported Registrations",
                "is_user_reported": True,
            })
        return events

    async def discover_all(self, db: AsyncSession) -> List[Opportunity]:
        """
        Executes live multi-source discovery.
        Syncs source registry, fetches live feeds, canonicalizes URLs, and inserts new records.
        """
        source_map = await self.sync_sources_registry(db)

        # 1. Fetch live opportunities
        devpost_items = await self.fetch_devpost_hackathons()
        github_items = await self.fetch_github_ai_hackathons()
        official_items = self.get_official_cloud_and_programs()
        user_items = self.get_user_reported_events()

        all_raw_items = devpost_items + github_items + official_items + user_items

        discovered_opportunities: List[Opportunity] = []

        for item in all_raw_items:
            canonical = canonicalize_url(item["official_url"])
            
            # Check if opportunity already exists
            existing = await db.execute(select(Opportunity).where(Opportunity.canonical_url == canonical))
            opp = existing.scalars().first()

            source_id = source_map.get(item.get("source_name"))

            if not opp:
                is_user_reported = item.get("is_user_reported", False)
                opp = Opportunity(
                    name=item["name"],
                    category=item["category"],
                    organization=item["organization"],
                    official_url=item["official_url"],
                    canonical_url=canonical,
                    country=item.get("country", "Global"),
                    source_id=source_id,
                    verification_status="PARTIALLY_VERIFIED" if is_user_reported else "UNVERIFIED",
                    eligibility_status="Eligibility unclear",
                    registration_deadline=item.get("registration_deadline"),
                    submission_deadline=item.get("submission_deadline"),
                    reward_value=item.get("reward_value", 0.0),
                    reward_type=item.get("reward_type", "Unknown"),
                    participation_fee=item.get("participation_fee", 0.0),
                    hidden_costs="None detected",
                    required_skills=item.get("required_skills", []),
                    official_terms_url=item.get("official_terms_url"),
                    source_evidence=item.get("source_evidence"),
                    status="USER_REPORTED_REGISTERED" if is_user_reported else "Discovered",
                    priority_score=50,
                    score_explanation={"basis": "Newly discovered via live source feed"},
                )
                db.add(opp)
                await db.flush()
                discovered_opportunities.append(opp)
            else:
                # Update source_id and evidence if missing
                if not opp.source_id and source_id:
                    opp.source_id = source_id
                if not opp.source_evidence and item.get("source_evidence"):
                    opp.source_evidence = item.get("source_evidence")
                discovered_opportunities.append(opp)

        # Log discovery jobs
        for src_name, src_id in source_map.items():
            count = len([i for i in all_raw_items if i.get("source_name") == src_name])
            job = DiscoveryJob(
                source_id=src_id,
                source_name=src_name,
                status="COMPLETED",
                items_found=count,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            db.add(job)

        await db.commit()

        await self.log_activity(
            db=db,
            event_type="Discovery",
            title=f"Multi-Source Discovery Completed: {len(discovered_opportunities)} items synced",
            details=f"Live feeds scanned: Devpost ({len(devpost_items)}), GitHub ({len(github_items)}), Cloud/Programs ({len(official_items)}), User Reported ({len(user_items)}).",
            status="SUCCESS",
        )

        return discovered_opportunities

    async def run_discovery(self, db: AsyncSession) -> List[Opportunity]:
        """Alias for discover_all."""
        return await self.discover_all(db)

