"""
Tests for Eligibility Engine and Arif Alam's Profile Rules
"""

import pytest
from hunter_ai.engines.eligibility import evaluate_eligibility
from hunter_ai.profile_data import USER_PROFILE


def test_nmims_distance_mba_qualifies_for_student_opportunities():
    """Rule: Treat NMIMS online/distance MBA enrolment as valid student status for initial screening."""
    student_opp = {
        "name": "GitHub Student Developer Pack",
        "category": "Student Benefits",
        "country": "Global",
        "required_skills": ["Git", "Python"],
        "official_terms_text": "Must be currently enrolled in a degree-granting course or university program.",
    }

    status, reasons = evaluate_eligibility(student_opp, USER_PROFILE)
    assert status in ["Eligible", "Likely eligible"]
    assert any("NMIMS" in r for r in reasons)


def test_india_residence_eligibility_global():
    opp = {
        "name": "Global AI Challenge",
        "category": "Hackathons",
        "country": "Global",
        "required_skills": ["Python", "Docker"],
        "description": "Open to participants worldwide.",
    }
    status, reasons = evaluate_eligibility(opp, USER_PROFILE)
    assert status == "Eligible"
    assert any("India" in r for r in reasons)


def test_us_only_restriction_flags_ineligible():
    opp = {
        "name": "US Local Dev Bounty",
        "category": "Cash Rewards",
        "country": "United States",
        "official_terms_text": "Only legal residents of US are eligible. US only.",
    }
    status, reasons = evaluate_eligibility(opp, USER_PROFILE)
    assert status == "Not eligible"
    assert any("US residents only" in r for r in reasons)


def test_working_professional_experience_match():
    opp = {
        "name": "Enterprise AI Architecture Summit",
        "category": "Events",
        "country": "India, Global",
        "required_skills": ["Python", "FastAPI", "Kubernetes"],
        "description": "For working professionals and experienced software developers.",
    }
    status, reasons = evaluate_eligibility(opp, USER_PROFILE)
    assert status == "Eligible"
    assert any("TCS" in r or "4.5" in r for r in reasons)
