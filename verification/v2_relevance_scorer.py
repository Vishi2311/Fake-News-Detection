"""
V2.6 Relevance Scorer

Calculates how strongly external evidence is related
to a submitted news claim.

Designed for:
- RSS headlines
- RSS summaries
- Fact-check articles
- Official sources
- News articles

Output:
0.0 -> 1.0
"""

import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):

    if not text:
        return ""

    text = str(text).lower()

    text = text.replace("’", "'")
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    # Keep letters, numbers, spaces and hyphens
    text = re.sub(
        r"[^a-z0-9\s-]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {
    "the", "a", "an",
    "and", "or", "but",
    "if", "then", "than",
    "that", "this", "these",
    "those", "is", "are",
    "was", "were", "be",
    "been", "being",
    "to", "of", "in",
    "on", "for", "from",
    "with", "by", "at",
    "as", "into", "about",
    "after", "before",
    "during", "over",
    "under", "up", "down",
    "it", "its",
    "he", "she",
    "they", "them",
    "his", "her",
    "their",
    "will", "would",
    "could", "should",
    "has", "have",
    "had", "do", "does",
    "did", "who", "what",
    "when", "where",
    "why", "how",

    # News-language words that shouldn't strongly
    # influence claim relevance
    "news",
    "report",
    "reports",
    "reported",
    "according",
    "says",
    "said",
    "latest",
    "today",
    "new",
    "update",
    "breaking"
}


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text):

    text = normalize_text(text)

    if not text:
        return set()

    return set(
        text.split()
    )


# ============================================================
# IMPORTANT WORDS
# ============================================================

def important_words(text):

    words = tokenize(text)

    return {
        word
        for word in words
        if (
            len(word) >= 4
            and word not in STOP_WORDS
        )
    }


# ============================================================
# IMPORTANT TERM NORMALIZATION
# ============================================================

def normalize_special_terms(words):

    result = set(words)

    # Artemis variations
    if (
        "artemis-ii" in result
        or "artemis-2" in result
    ):
        result.add("artemis")

    # International Criminal Court
    if (
        "international" in result
        and "criminal" in result
        and "court" in result
    ):
        result.add("icc")

    # NASA
    if "nasa" in result:
        result.add("nasa")

    return result


# ============================================================
# ENTITY EXTRACTION
# ============================================================

def extract_entities(text):

    if not text:
        return set()

    original = str(text)

    matches = re.findall(
        r"\b[A-Z][A-Za-z0-9-]*(?:\s+[A-Z][A-Za-z0-9-]*)*\b",
        original
    )

    entities = set()

    for match in matches:

        normalized = normalize_text(
            match
        )

        if (
            len(normalized) >= 3
            and normalized not in STOP_WORDS
        ):
            entities.add(
                normalized
            )

    return entities


# ============================================================
# SPECIAL HIGH-VALUE ENTITIES
# ============================================================

HIGH_VALUE_ENTITIES = {
    "nasa",
    "artemis",
    "artemis ii",
    "artemis 2",
    "moon",
    "mars",

    "trump",
    "donald trump",

    "duterte",
    "rodrigo duterte",

    "icc",
    "international criminal court",

    "india",
    "china",
    "russia",
    "ukraine",

    "israel",
    "palestine",

    "president",
    "prime minister",
    "government",

    "election",
    "elections",

    "parliament",
    "senate",
    "supreme court"
}


# ============================================================
# SPECIAL TERM SCORE
# ============================================================

def special_term_score(
    claim,
    evidence
):

    claim_words = normalize_special_terms(
        important_words(claim)
    )

    evidence_words = normalize_special_terms(
        important_words(evidence)
    )

    if not claim_words:
        return 0.0

    claim_special = (
        claim_words
        & {
            "nasa",
            "artemis",
            "moon",
            "mars",
            "trump",
            "duterte",
            "icc",
            "international",
            "criminal",
            "court",
            "india",
            "china",
            "russia",
            "ukraine",
            "israel",
            "palestine",
            "president",
            "minister",
            "government",
            "election",
            "elections",
            "parliament",
            "senate",
            "supreme"
        }
    )

    if not claim_special:
        return 0.0

    matched = (
        claim_special
        & evidence_words
    )

    return min(
        len(matched)
        / len(claim_special),
        1.0
    )


# ============================================================
# KEYWORD OVERLAP
# ============================================================

def keyword_overlap_score(
    claim,
    evidence
):

    claim_words = important_words(
        claim
    )

    evidence_words = important_words(
        evidence
    )

    if not claim_words:
        return 0.0

    matched = (
        claim_words
        & evidence_words
    )

    return min(
        len(matched)
        / len(claim_words),
        1.0
    )


# ============================================================
# ENTITY MATCH
# ============================================================

def entity_match_score(
    claim,
    evidence
):

    claim_entities = extract_entities(
        claim
    )

    evidence_entities = extract_entities(
        evidence
    )

    if not claim_entities:
        return 0.0

    matched = 0

    for entity in claim_entities:

        if entity in evidence_entities:

            matched += 1
            continue

        entity_words = set(
            entity.split()
        )

        for evidence_entity in evidence_entities:

            evidence_words = set(
                evidence_entity.split()
            )

            if (
                entity_words
                and evidence_words
                and (
                    entity_words
                    <= evidence_words
                    or
                    evidence_words
                    <= entity_words
                )
            ):

                matched += 1
                break

    return min(
        matched / len(claim_entities),
        1.0
    )


# ============================================================
# PHRASE EXTRACTION
# ============================================================

def extract_phrases(text):

    normalized = normalize_text(
        text
    )

    words = normalized.split()

    phrases = set()

    for i in range(
        len(words) - 1
    ):

        first = words[i]
        second = words[i + 1]

        if (
            len(first) >= 3
            and len(second) >= 3
        ):

            phrases.add(
                first
                + " "
                + second
            )

    return phrases


# ============================================================
# PHRASE MATCH
# ============================================================

def phrase_match_score(
    claim,
    evidence
):

    claim_phrases = extract_phrases(
        claim
    )

    evidence_phrases = extract_phrases(
        evidence
    )

    if not claim_phrases:
        return 0.0

    matched = (
        claim_phrases
        & evidence_phrases
    )

    return min(
        len(matched)
        / len(claim_phrases),
        1.0
    )


# ============================================================
# TF-IDF SIMILARITY
# ============================================================

def tfidf_similarity(
    claim,
    evidence
):

    claim = normalize_text(
        claim
    )

    evidence = normalize_text(
        evidence
    )

    if not claim or not evidence:
        return 0.0

    try:

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1
        )

        matrix = vectorizer.fit_transform(
            [
                claim,
                evidence
            ]
        )

        score = cosine_similarity(
            matrix[0:1],
            matrix[1:2]
        )[0][0]

        return float(
            max(
                0.0,
                min(
                    score,
                    1.0
                )
            )
        )

    except Exception:

        return 0.0


# ============================================================
# TITLE MATCH
# ============================================================

def title_match_score(
    claim,
    title
):

    if not title:
        return 0.0

    claim_words = important_words(
        claim
    )

    title_words = important_words(
        title
    )

    if not claim_words:
        return 0.0

    matched = (
        claim_words
        & title_words
    )

    return min(
        len(matched)
        / len(claim_words),
        1.0
    )


# ============================================================
# FACT CHECK DETECTION
# ============================================================

def is_fact_check_text(text):

    text = normalize_text(
        text
    )

    fact_check_terms = [
        "fact check",
        "fact-check",
        "debunked",
        "debunk",
        "false claim",
        "fake claim",
        "fake news",
        "false information",
        "misleading claim",
        "hoax",
        "not true",
        "no evidence",
        "did not happen",
        "never happened"
    ]

    return any(
        term in text
        for term in fact_check_terms
    )


# ============================================================
# CALCULATE RELEVANCE
# ============================================================

def calculate_relevance_v2(
    claim,
    evidence_title="",
    evidence_text=""
):

    claim = str(
        claim or ""
    )

    evidence_title = str(
        evidence_title or ""
    )

    evidence_text = str(
        evidence_text or ""
    )

    combined = (
        evidence_title
        + " "
        + evidence_text
    ).strip()

    if not claim or not combined:
        return 0.0

    # --------------------------------------------------------
    # COMPONENT SCORES
    # --------------------------------------------------------

    keyword_score = keyword_overlap_score(
        claim,
        combined
    )

    entity_score = entity_match_score(
        claim,
        combined
    )

    phrase_score = phrase_match_score(
        claim,
        combined
    )

    tfidf_score = tfidf_similarity(
        claim,
        combined
    )

    title_score = title_match_score(
        claim,
        evidence_title
    )

    special_score = special_term_score(
        claim,
        combined
    )

    # --------------------------------------------------------
    # BASE SCORE
    # --------------------------------------------------------

    score = (

        0.25 * keyword_score

        + 0.20 * entity_score

        + 0.15 * phrase_score

        + 0.15 * tfidf_score

        + 0.15 * title_score

        + 0.10 * special_score
    )

    # --------------------------------------------------------
    # ENTITY + TITLE BOOST
    # --------------------------------------------------------

    if (
        entity_score >= 0.50
        and title_score >= 0.25
    ):

        score += 0.10

    # --------------------------------------------------------
    # SPECIAL ENTITY BOOST
    # --------------------------------------------------------

    if special_score >= 0.50:

        score += 0.08

    # --------------------------------------------------------
    # FACT CHECK BOOST
    # --------------------------------------------------------

    # Fact-check evidence is particularly valuable,
    # but only when it is actually about the submitted claim.

    if is_fact_check_text(
        combined
    ):

        if (
            entity_score >= 0.25
            or special_score >= 0.50
            or title_score >= 0.20
        ):

            score += 0.12

    # --------------------------------------------------------
    # STRONG DIRECT MATCH
    # --------------------------------------------------------

    if (
        keyword_score >= 0.60
        and (
            entity_score >= 0.40
            or special_score >= 0.50
        )
    ):

        score += 0.08

    # --------------------------------------------------------
    # UNRELATED EVIDENCE PENALTY
    # --------------------------------------------------------

    if (
        keyword_score < 0.10
        and entity_score < 0.10
        and special_score < 0.20
    ):

        score *= 0.60

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

    score = max(
        0.0,
        min(
            score,
            1.0
        )
    )

    return round(
        score,
        4
    )


# ============================================================
# COMPATIBILITY FUNCTION
# ============================================================

def calculate_relevance(
    claim,
    evidence_title="",
    evidence_text=""
):

    return calculate_relevance_v2(
        claim,
        evidence_title,
        evidence_text
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    tests = [

        (
            "NASA launches astronauts on Artemis II mission to the Moon",
            "NASA's Artemis II mission will take an astronaut crew around the Moon"
        ),

        (
            "Trump ordered Duterte release from International Criminal Court",
            "FACT CHECK: News graphic claiming ICC will release Duterte is fake"
        ),

        (
            "India will build a permanent city on Mars by 2030",
            "Nasa unveils next steps to build permanent Moon base"
        )
    ]

    print(
        "V2 RELEVANCE SCORER TEST"
    )

    print(
        "=================================================="
    )

    for claim, evidence in tests:

        score = calculate_relevance_v2(
            claim,
            evidence,
            ""
        )

        print(
            "\nClaim:"
        )

        print(claim)

        print(
            "\nEvidence:"
        )

        print(evidence)

        print(
            f"\nRelevance: {score:.2f}"
        )

        print(
            "--------------------------------------------------"
        )