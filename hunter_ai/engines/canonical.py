"""
Canonical URL Normalization & Deduplication Engine
Prevents duplicate opportunities by standardizing URLs, domain names,
and event names across scrapers, APIs, and feeds.
"""

import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import hashlib


TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "ref",
    "source",
    "affiliate",
    "source_id",
}


def canonicalize_url(url: str) -> str:
    """
    Standardize a URL:
    - Lowercase scheme and netloc
    - Strip common tracking and affiliate parameters
    - Remove fragment / anchor
    - Normalize trailing slashes
    """
    if not url:
        return ""
    
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    # Strip port if standard
    if (scheme == "http" and netloc.endswith(":80")) or (scheme == "https" and netloc.endswith(":443")):
        netloc = netloc.rsplit(":", 1)[0]
    
    # Strip www prefix for consistent matching where applicable
    if netloc.startswith("www."):
        netloc = netloc[4:]

    # Filter query parameters
    filtered_queries = []
    if parsed.query:
        for k, v in parse_qsl(parsed.query, keep_blank_values=False):
            if k.lower() not in TRACKING_PARAMS:
                filtered_queries.append((k, v))
    
    # Sort query params for deterministic output
    filtered_queries.sort(key=lambda x: x[0])
    new_query = urlencode(filtered_queries)

    # Normalize path
    path = (parsed.path or "/").lower()
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    canonical = urlunparse((scheme, netloc, path, "", new_query, ""))
    return canonical


def generate_opportunity_fingerprint(name: str, organization: str, official_url: str) -> str:
    """
    Generates a unique deterministic SHA-256 fingerprint for deduplication.
    Uses canonical URL and simplified name/org.
    """
    c_url = canonicalize_url(official_url)
    clean_name = re.sub(r"[^a-z0-9]", "", name.lower())
    clean_org = re.sub(r"[^a-z0-9]", "", organization.lower())
    
    raw = f"{c_url}|{clean_name}|{clean_org}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
