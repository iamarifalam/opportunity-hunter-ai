"""
Tests for Canonical URL Normalization and Opportunity Deduplication
"""

import pytest
from hunter_ai.engines.canonical import canonicalize_url, generate_opportunity_fingerprint


def test_canonicalize_url_strips_tracking_params():
    url_with_utm = "https://ai.google.dev/competition?utm_source=twitter&utm_medium=social&utm_campaign=hackathon2026&ref=dev_newsletter"
    clean_url = canonicalize_url(url_with_utm)
    assert "utm_source" not in clean_url
    assert "utm_medium" not in clean_url
    assert "ref" not in clean_url
    assert clean_url == "https://ai.google.dev/competition"


def test_canonicalize_url_normalizes_trailing_slash_and_case():
    url1 = "https://AWS.Amazon.COM/Activate/Founders/"
    url2 = "http://aws.amazon.com:80/activate/founders"
    assert canonicalize_url(url1) == "https://aws.amazon.com/activate/founders"
    assert canonicalize_url(url2) == "http://aws.amazon.com/activate/founders"


def test_generate_opportunity_fingerprint_deterministic():
    fp1 = generate_opportunity_fingerprint(
        name="Gemini AI Competition",
        organization="Google",
        official_url="https://ai.google.dev/competition?utm_source=reddit",
    )
    fp2 = generate_opportunity_fingerprint(
        name="gemini ai competition",
        organization="Google",
        official_url="https://ai.google.dev/competition",
    )
    assert fp1 == fp2
