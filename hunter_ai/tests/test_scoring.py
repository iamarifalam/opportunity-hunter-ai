"""
Tests for AI Opportunity Scoring Engine (0 - 100)
"""

import pytest
from hunter_ai.engines.scoring import calculate_opportunity_score


def test_high_value_cash_and_cloud_credits_score_high():
    opp = {
        "name": "Global GenAI Autonomous Agents Hackathon",
        "category": "Hackathons",
        "organization": "Google DeepMind",
        "reward_value": 50000.0,
        "reward_type": "Cash Prize & Cloud Credits",
        "participation_fee": 0.0,
        "description": "Build agentic workflows with LangGraph, MCP, RAG, and FastAPI.",
    }

    score, explanation = calculate_opportunity_score(opp, eligibility_status="Eligible")
    assert score >= 80
    assert "breakdown" in explanation
    assert explanation["breakdown"]["free_participation"]["points"] == 15
    assert explanation["breakdown"]["eligibility"]["points"] == 25


def test_ineligible_opportunity_scores_low():
    opp = {
        "name": "Local High School Robotics Competition",
        "category": "Gadgets",
        "organization": "Local High School",
        "reward_value": 50.0,
        "reward_type": "Swag",
        "participation_fee": 0.0,
        "description": "High school robotics.",
    }

    score, explanation = calculate_opportunity_score(opp, eligibility_status="Not eligible")
    assert score < 50
    assert explanation["breakdown"]["eligibility"]["points"] == 0
