"""
Creator and Ambassador Agent for Opportunity Hunter AI.
Finds and monitors high-value creator initiatives, technical book reviewer roles,
ambassador kits, speaking engagements, and sponsored travel matching 'Data Science Reality'.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from hunter_ai.agents.base import BaseAgent
from hunter_ai.engines.canonical import canonicalize_url
from hunter_ai.models import Opportunity, Source
from hunter_ai.profile_data import USER_PROFILE


VERIFIED_CREATOR_PROGRAMS = [
    {
        "name": "Packt Publishing Technical Reviewer Program",
        "organization": "Packt Publishing",
        "category": "Creator Programs",
        "official_url": "https://authors.packtpub.com/tech-reviewers/",
        "canonical_url": "https://authors.packtpub.com/tech-reviewers/",
        "description": "Review upcoming technical books and video courses in AI Engineering, Generative AI, RAG, and Python. Receive complimentary technical books, free subscription access to the entire Packt library, and author honorariums.",
        "reward_type": "Free Technical Books & Honorarium",
        "reward_value": 300.0,
        "deadline": "Rolling",
        "participation_fee": "$0.00 (Zero Fee)",
        "terms_and_conditions": "Open to technical professionals with domain expertise in AI/ML. Reviewer feedback submitted via chapter milestones.",
        "rules_summary": "100% free participation. Reviewers retain credit on published books.",
    },
    {
        "name": "O'Reilly Media Early Release Reviewer Initiative",
        "organization": "O'Reilly Media",
        "category": "Creator Programs",
        "official_url": "https://www.oreilly.com/work-with-us.html",
        "canonical_url": "https://www.oreilly.com/work-with-us.html#review",
        "description": "Provide early technical peer review on books covering Agentic AI, LLM System Architecture, and Cloud Native DevOps. Reviewers receive free 1-year O'Reilly Learning Platform subscriptions.",
        "reward_type": "O'Reilly Subscription ($499 Value) & Print Books",
        "reward_value": 499.0,
        "deadline": "Rolling",
        "participation_fee": "$0.00 (Zero Fee)",
        "terms_and_conditions": "Reviewers must provide feedback on draft chapters. No financial commitment required.",
        "rules_summary": "Zero cost. High alignment with AI Engineer background.",
    },
    {
        "name": "Postman Supernova Community Ambassador",
        "organization": "Postman",
        "category": "Creator Programs",
        "official_url": "https://www.postman.com/community/supernovas/",
        "canonical_url": "https://www.postman.com/community/supernovas/",
        "description": "Global advocacy program for content creators, meetup organizers, and API enthusiasts. Benefits include sponsored event support, exclusive swag packages, direct access to Postman engineering team, and speaking opportunities.",
        "reward_type": "Ambassador Swag & Event Sponsorship",
        "reward_value": 250.0,
        "deadline": "Rolling",
        "participation_fee": "$0.00 (Zero Fee)",
        "terms_and_conditions": "Active technical creators sharing tutorials or hosting community events. India candidates fully eligible.",
        "rules_summary": "Exclusive developer merchandise shipped to India at zero cost.",
    },
    {
        "name": "Manning Publications Early Access Program Reviewer",
        "organization": "Manning Publications",
        "category": "Creator Programs",
        "official_url": "https://www.manning.com/review",
        "canonical_url": "https://www.manning.com/review",
        "description": "Review chapters of books in progress (MEAP). In return, receive free digital copies of finished books and Manning tokens redeemable for print books and courses.",
        "reward_type": "Free Manning Books & Course Tokens",
        "reward_value": 200.0,
        "deadline": "Rolling",
        "participation_fee": "$0.00 (Zero Fee)",
        "terms_and_conditions": "Requires detailed constructive technical feedback on chapter drafts.",
        "rules_summary": "Zero cost, high value for continuous learning in AI and software engineering.",
    },
    {
        "name": "PyCon India Speaker Call for Proposals & Travel Grant",
        "organization": "Python India",
        "category": "Events & Travel",
        "official_url": "https://in.pycon.org",
        "canonical_url": "https://in.pycon.org/#travel-grants",
        "description": "Annual premier Python conference in India. Accepted speakers receive free full conference access, speaker dinner, and financial aid grants covering travel and accommodation.",
        "reward_type": "Free Conference Pass + Travel & Hotel Grant",
        "reward_value": 350.0,
        "deadline": "2026-07-31",
        "participation_fee": "$0.00 (Zero Fee)",
        "terms_and_conditions": "Proposals submitted via official CFP portal. Financial aid prioritized for speakers and community contributors.",
        "rules_summary": "Zero cost for accepted speakers; sponsored travel within India.",
    },
]


class CreatorAgent(BaseAgent):
    """
    Dedicated agent for technical creator programs, reviewer initiatives, and ambassador perks.
    """

    def __init__(self):
        super().__init__(name="CreatorAgent")

    async def sync_creator_opportunities(self, db: AsyncSession) -> List[Opportunity]:
        """
        Synchronizes verified creator programs into the `opportunities` database.
        """
        synced = []
        for item in VERIFIED_CREATOR_PROGRAMS:
            canonical = canonicalize_url(item["canonical_url"])
            res = await db.execute(
                select(Opportunity).where(Opportunity.canonical_url == canonical)
            )
            existing = res.scalars().first()

            if existing:
                existing.description = item["description"]
                existing.reward_type = item["reward_type"]
                existing.reward_value = item["reward_value"]
                existing.rules_summary = item["rules_summary"]
                synced.append(existing)
            else:
                opp = Opportunity(
                    name=item["name"],
                    organization=item["organization"],
                    canonical_url=canonical,
                    official_url=item["official_url"],
                    category=item["category"],
                    description=item["description"],
                    reward_type=item["reward_type"],
                    reward_value=item["reward_value"],
                    currency="USD",
                    participation_fee=0.0,
                    terms_and_conditions=item["terms_and_conditions"],
                    rules_summary=item["rules_summary"],
                    deadline=item["deadline"],
                    status="Discovered",
                    verification_status="VERIFIED",
                    source_name=item["organization"],
                )
                db.add(opp)
                synced.append(opp)

        await db.commit()
        for opp in synced:
            await db.refresh(opp)

        await self.log_activity(
            db,
            event_type="CREATOR_SYNC_COMPLETED",
            title=f"Creator Agent Synced {len(synced)} Verified Creator Programs",
            details="Aligned with Data Science Reality creator niche and AI engineering skills.",
            status="SUCCESS",
        )
        return synced
