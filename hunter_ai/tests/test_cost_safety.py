"""
Tests for Cost & Safety Policy Engine (Strict Zero-Cost Rule)
"""

import pytest
from hunter_ai.engines.cost_safety import evaluate_cost_safety


def test_free_opportunity_passes_safety_check():
    result = evaluate_cost_safety(
        participation_fee=0.0,
        terms_text="100% free registration. No cost or purchase required.",
        description_text="Free AI hackathon with sponsored cloud credits.",
        requires_credit_card=False,
    )
    assert result.is_safe is True
    assert result.participation_fee == 0.0
    assert len(result.flags) == 0


def test_explicit_participation_fee_fails_safety_check():
    result = evaluate_cost_safety(
        participation_fee=49.99,
        terms_text="Standard developer ticket.",
        description_text="Tech conference with entry pass.",
    )
    assert result.is_safe is False
    assert any("Explicit participation fee charged" in f for f in result.flags)


def test_hidden_credit_card_or_trial_billing_fails_safety_check():
    result = evaluate_cost_safety(
        participation_fee=0.0,
        terms_text="First month free then auto-renews at $29/month. Credit card required to activate account.",
        description_text="Cloud trial program.",
        requires_credit_card=True,
    )
    assert result.is_safe is False
    assert any("credit card" in f.lower() or "billing" in f.lower() or "renews" in f.lower() for f in result.flags)
