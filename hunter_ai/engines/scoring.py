"""
AI Opportunity Scoring Engine (0 - 100)
Calculates a multi-dimensional composite priority score for Arif Alam,
with special weighting for Cash rewards, Cloud/GPU credits, AI API credits,
free certifications, high-impact hackathons, and creator value.
Includes a transparent rationale breakdown.
"""

from typing import Dict, Any, Tuple
from datetime import datetime, timezone


def calculate_opportunity_score(
    opportunity_data: Dict[str, Any],
    eligibility_status: str = "Eligible",
) -> Tuple[int, Dict[str, Any]]:
    """
    Computes priority score (0-100) and rationale components:
    - Eligibility Match (max 25)
    - Reward Value & Type (max 25)
    - Free Participation (max 15)
    - AI Career Alignment (max 15)
    - Creator & Community Impact (max 10)
    - Urgency & Credibility (max 10)
    """
    category = opportunity_data.get("category", "")
    reward_type = opportunity_data.get("reward_type", "")
    reward_value = float(opportunity_data.get("reward_value", 0.0))
    participation_fee = float(opportunity_data.get("participation_fee", 0.0))
    organization = opportunity_data.get("organization", "").lower()
    description = (opportunity_data.get("description", "") + " " + opportunity_data.get("name", "")).lower()
    
    breakdown = {}

    # 1. Eligibility Score (0 - 25)
    if eligibility_status == "Eligible":
        eligibility_score = 25
        eligibility_note = "Full eligibility verified (India resident, student/pro status, skills match)"
    elif eligibility_status == "Likely eligible":
        eligibility_score = 18
        eligibility_note = "High likelihood of eligibility with minor secondary terms to verify"
    elif eligibility_status == "Eligibility unclear":
        eligibility_score = 10
        eligibility_note = "Ambiguous terms requiring review"
    else:
        eligibility_score = 0
        eligibility_note = "Ineligible based on country, experience, or student restrictions"
    breakdown["eligibility"] = {"points": eligibility_score, "max": 25, "note": eligibility_note}

    # 2. Reward Value & Type (0 - 25)
    reward_score = 0
    reward_notes = []

    # Priority category bonus: Cash, Cloud Credits, AI Credits, Certifications
    high_priority_categories = ["Cash Rewards", "Cloud Credits", "AI Credits", "Certifications", "Hackathons"]
    if category in high_priority_categories:
        reward_score += 10
        reward_notes.append(f"High-priority category '{category}' (+10)")

    # Reward Type specific value
    if "cash" in reward_type.lower() or "bounty" in reward_type.lower() or "grant" in reward_type.lower():
        reward_score += 8
        reward_notes.append("Direct monetary prize / grant reward (+8)")
    elif "gpu" in reward_type.lower() or "cloud" in reward_type.lower() or "credits" in reward_type.lower():
        reward_score += 8
        reward_notes.append("High-value Cloud / GPU / AI inference credits (+8)")
    elif "certification" in reward_type.lower():
        reward_score += 7
        reward_notes.append("Professional industry certification voucher (+7)")
    elif "gadget" in reward_type.lower() or "hardware" in reward_type.lower():
        reward_score += 6
        reward_notes.append("Hardware / gadget award (+6)")
    else:
        reward_score += 4
        reward_notes.append("General developer perk / access (+4)")

    # Reward scale
    if reward_value >= 5000:
        reward_score += 7
        reward_notes.append(f"Substantial reward tier (${reward_value:,.0f}+) (+7)")
    elif reward_value >= 1000:
        reward_score += 5
        reward_notes.append(f"Valuable reward tier (${reward_value:,.0f}) (+5)")
    elif reward_value > 0:
        reward_score += 3
        reward_notes.append(f"Reward tier (${reward_value:,.0f}) (+3)")

    reward_score = min(25, reward_score)
    breakdown["reward"] = {"points": reward_score, "max": 25, "note": "; ".join(reward_notes)}

    # 3. Free Participation Policy (0 - 15)
    if participation_fee == 0.0:
        fee_score = 15
        fee_note = "100% Free entry, zero cost, no card required"
    else:
        fee_score = 0
        fee_note = f"Non-free participation fee (${participation_fee}) violates zero-cost rule"
    breakdown["free_participation"] = {"points": fee_score, "max": 15, "note": fee_note}

    # 4. AI Career Relevance (0 - 15)
    career_score = 0
    career_notes = []
    ai_keywords = [
        "agentic", "agent", "genai", "generative ai", "rag", "mcp", "a2a",
        "llm", "large language model", "fastapi", "docker", "kubernetes",
        "mlops", "langchain", "langgraph", "deep learning", "nlp"
    ]
    matched_keywords = [kw for kw in ai_keywords if kw in description]
    if len(matched_keywords) >= 3:
        career_score = 15
        career_notes.append(f"Direct match with core stack: {', '.join(matched_keywords[:4])}")
    elif len(matched_keywords) >= 1:
        career_score = 10
        career_notes.append(f"Relevant tech stack: {', '.join(matched_keywords)}")
    elif category in ["Hackathons", "AI Credits", "Cloud Credits"]:
        career_score = 8
        career_notes.append("General technology / AI engineering relevance")
    else:
        career_score = 5
        career_notes.append("Adjacent software engineering relevance")
    breakdown["career_relevance"] = {"points": career_score, "max": 15, "note": "; ".join(career_notes)}

    # 5. Creator & Community Relevance (0 - 10)
    creator_score = 0
    creator_notes = []
    if category in ["Creator Programs"] or any(k in description for k in ["ambassador", "speaker", "community", "technical reviewer", "book reviewer"]):
        creator_score = 10
        creator_notes.append("High synergy with 'Data Science Reality' brand and technical teaching")
    elif any(k in description for k in ["share", "blog", "showcase", "open source", "demo"]):
        creator_score = 7
        creator_notes.append("Good showcase potential for LinkedIn / community audience")
    else:
        creator_score = 4
        creator_notes.append("Standard developer competition")
    breakdown["creator_relevance"] = {"points": creator_score, "max": 10, "note": "; ".join(creator_notes)}

    # 6. Organizer Credibility & Feasibility (0 - 10)
    credibility_score = 5
    prestigious_orgs = [
        "google", "microsoft", "aws", "amazon", "nvidia", "meta", "openai", "anthropic",
        "hugging face", "github", "cohere", "mistral", "groq", "tcs", "nmims", "devpost", "kaggle"
    ]
    if any(org in organization for org in prestigious_orgs):
        credibility_score += 4
        cred_note = f"Established global tech organizer: {organization.title()}"
    else:
        cred_note = "Verified legitimate organizer"

    # Deadline urgency check
    dl_str = opportunity_data.get("registration_deadline")
    if dl_str:
        try:
            dl_dt = datetime.fromisoformat(dl_str.replace("Z", "+00:00"))
            days_left = (dl_dt - datetime.now(timezone.utc)).total_seconds() / 86400.0
            if 0 < days_left <= 7:
                credibility_score += 1
                cred_note += f"; Approaching deadline ({int(days_left)} days remaining)"
        except Exception:
            pass

    credibility_score = min(10, credibility_score)
    breakdown["credibility_urgency"] = {"points": credibility_score, "max": 10, "note": cred_note}

    total_score = eligibility_score + reward_score + fee_score + career_score + creator_score + credibility_score

    # Construct human-readable explanation
    explanation_summary = (
        f"Score {total_score}/100: {eligibility_note}. {breakdown['reward']['note']}. "
        f"{fee_note}. Career alignment: {breakdown['career_relevance']['note']}."
    )

    full_explanation = {
        "total_score": total_score,
        "summary": explanation_summary,
        "breakdown": breakdown,
    }

    return total_score, full_explanation
