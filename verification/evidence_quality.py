import re
from urllib.parse import urlparse


# ============================================================
# V2.1 EVIDENCE QUALITY FILTER
# ============================================================

SOCIAL_DOMAINS = {
    "facebook.com",
    "www.facebook.com",
    "x.com",
    "www.x.com",
    "twitter.com",
    "www.twitter.com",
    "instagram.com",
    "www.instagram.com",
    "tiktok.com",
    "www.tiktok.com",
    "youtube.com",
    "www.youtube.com",
}


# Domains that commonly publish syndicated/reposted material.
# These are NOT automatically considered false.
# They are simply given lower independence value.
SYNDICATION_INDICATORS = {
    "news.google.com",
}


def normalize_domain(url):
    """
    Return a clean domain name.

    Example:
        https://www.apnews.com/article/abc
        -> apnews.com
    """

    if not url:
        return ""

    try:
        domain = urlparse(url).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:
        return ""


def get_root_domain(domain):
    """
    Simplified root-domain extraction.

    Examples:
        www.apnews.com -> apnews.com
        apnews.com     -> apnews.com
    """

    if not domain:
        return ""

    domain = domain.lower().strip()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def is_social_source(domain):
    """
    Check whether a source is a social-media platform.
    """

    domain = get_root_domain(domain)

    return (
        domain in SOCIAL_DOMAINS
        or domain.endswith(".facebook.com")
        or domain.endswith(".twitter.com")
        or domain.endswith(".instagram.com")
        or domain.endswith(".tiktok.com")
    )


def normalize_title(title):
    """
    Normalize article title for duplicate comparison.
    """

    if not title:
        return ""

    title = title.lower()

    # Remove punctuation
    title = re.sub(r"[^a-z0-9\s]", " ", title)

    # Normalize whitespace
    title = re.sub(r"\s+", " ", title).strip()

    return title


def title_tokens(title):
    """
    Return meaningful title tokens.
    """

    normalized = normalize_title(title)

    if not normalized:
        return set()

    stopwords = {
        "the",
        "a",
        "an",
        "of",
        "to",
        "in",
        "on",
        "for",
        "and",
        "with",
        "as",
        "at",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
    }

    return {
        word
        for word in normalized.split()
        if word not in stopwords
    }


def title_similarity(title_a, title_b):
    """
    Simple Jaccard similarity between two titles.
    """

    a = title_tokens(title_a)
    b = title_tokens(title_b)

    if not a or not b:
        return 0.0

    intersection = len(a & b)
    union = len(a | b)

    if union == 0:
        return 0.0

    return intersection / union


def is_probable_duplicate(item, existing_items):
    """
    Detect whether an evidence item is probably a duplicate
    of an already selected evidence item.

    Duplicate detection considers:

    1. Same domain + highly similar title
    2. Very similar title across different domains
    """

    title = item.get("title", "")
    domain = get_root_domain(
        item.get("source", "")
        or item.get("domain", "")
    )

    for existing in existing_items:

        existing_title = existing.get("title", "")

        existing_domain = get_root_domain(
            existing.get("source", "")
            or existing.get("domain", "")
        )

        similarity = title_similarity(
            title,
            existing_title
        )

        # Same publisher + almost identical title
        if (
            domain
            and existing_domain
            and domain == existing_domain
            and similarity >= 0.70
        ):
            return True

        # Different publisher but almost identical headline.
        # This catches syndicated copies.
        if similarity >= 0.90:
            return True

    return False


def calculate_independence_score(item):
    """
    Estimate how independently useful an evidence item is.

    This is separate from source trust.

    Trust:
        Is the publisher generally reliable?

    Independence:
        Is this actually an independent piece of evidence?
    """

    domain = get_root_domain(
        item.get("source", "")
        or item.get("domain", "")
    )

    score = 1.0

    # Social media reposts are not independent reporting.
    if is_social_source(domain):
        return 0.0

    # Google News itself is an aggregator.
    if domain in SYNDICATION_INDICATORS:
        return 0.20

    # RSS result pointing toward a publisher is potentially useful,
    # but still slightly less independent than direct article content.
    evidence_type = str(
        item.get("type", "")
    ).upper()

    if evidence_type == "RSS_SUMMARY":
        score *= 0.90

    return round(score, 4)


def classify_evidence_quality(item):
    """
    Add V2.1 evidence-quality metadata.
    """

    domain = get_root_domain(
        item.get("source", "")
        or item.get("domain", "")
    )

    independence = calculate_independence_score(item)

    if independence == 0:
        quality = "SOCIAL_REPOST"

    elif independence < 0.5:
        quality = "AGGREGATOR"

    elif item.get("trusted_source", False):
        quality = "TRUSTED_INDEPENDENT"

    else:
        quality = "INDEPENDENT"

    item["normalized_domain"] = domain
    item["independence_score"] = independence
    item["evidence_quality"] = quality

    return item


def filter_evidence(evidence):
    """
    Main V2.1 filtering function.

    Returns:

        filtered_evidence
        quality_statistics
    """

    if not evidence:
        return [], {
            "raw_evidence": 0,
            "filtered_evidence": 0,
            "duplicates_removed": 0,
            "social_removed": 0,
            "independent_sources": 0,
            "trusted_independent_sources": 0,
        }

    processed = []

    duplicates_removed = 0
    social_removed = 0

    # --------------------------------------------------------
    # First pass: classify every item
    # --------------------------------------------------------

    for item in evidence:

        item = classify_evidence_quality(item)

        # Remove social-media reposts.
        if item["evidence_quality"] == "SOCIAL_REPOST":
            social_removed += 1
            continue

        processed.append(item)

    # --------------------------------------------------------
    # Second pass: remove duplicates
    # --------------------------------------------------------

    filtered = []

    for item in processed:

        if is_probable_duplicate(item, filtered):

            duplicates_removed += 1
            continue

        filtered.append(item)

    # --------------------------------------------------------
    # Count independent sources
    # --------------------------------------------------------

    independent_domains = set()
    trusted_domains = set()

    for item in filtered:

        domain = item.get(
            "normalized_domain",
            ""
        )

        independence = item.get(
            "independence_score",
            0
        )

        if independence >= 0.70 and domain:
            independent_domains.add(domain)

        if (
            independence >= 0.70
            and item.get("trusted_source", False)
            and domain
        ):
            trusted_domains.add(domain)

    statistics = {
        "raw_evidence": len(evidence),
        "filtered_evidence": len(filtered),
        "duplicates_removed": duplicates_removed,
        "social_removed": social_removed,
        "independent_sources": len(independent_domains),
        "trusted_independent_sources": len(trusted_domains),
    }

    return filtered, statistics