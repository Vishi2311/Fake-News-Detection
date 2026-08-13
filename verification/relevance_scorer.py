
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


STOP_WORDS = {
    "the", "a", "an", "and", "or", "is", "are",
    "was", "were", "to", "of", "in", "on", "for",
    "with", "by", "from", "this", "that", "new",
    "any", "has", "have", "had"
}


# Words that commonly represent the same concept
RELATED_WORDS = {
    "weather": {
        "weather", "forecast", "rain", "rainfall",
        "storm", "storms", "thunderstorm", "showers",
        "heatwave", "temperature", "monsoon",
        "imd", "winds"
    },

    "mission": {
        "mission", "missions", "launch", "lander",
        "landings", "spacecraft", "moon", "lunar",
        "artemis"
    },

    "delhi": {
        "delhi", "delhi-ncr", "ncr", "noida",
        "ghaziabad", "gurgaon", "gurugram"
    }
}


def tokenize(text):
    """Extract useful words from text."""

    words = re.findall(
        r"[a-zA-Z0-9-]+",
        text.lower()
    )

    return {
        word
        for word in words
        if len(word) > 2 and word not in STOP_WORDS
    }


def get_concept_matches(claim_words, evidence_words):
    """
    Check whether words belong to the same important concept.
    """

    score = 0

    for group in RELATED_WORDS.values():

        claim_has_group = bool(
            claim_words.intersection(group)
        )

        evidence_has_group = bool(
            evidence_words.intersection(group)
        )

        if claim_has_group and evidence_has_group:
            score += 1

    return score


def calculate_relevance(claim, evidence_title):
    """
    Calculate relevance using:

    1. Exact phrase matching
    2. Keyword overlap
    3. Related concept matching
    4. TF-IDF similarity
    """

    if not claim or not evidence_title:
        return 0.0

    claim_clean = claim.lower().strip()
    evidence_clean = evidence_title.lower().strip()

    claim_words = tokenize(claim_clean)
    evidence_words = tokenize(evidence_clean)

    if not claim_words or not evidence_words:
        return 0.0

    # --------------------------------
    # 1. Exact phrase match
    # --------------------------------

    exact_match = (
        claim_clean in evidence_clean
    )

    # --------------------------------
    # 2. Direct keyword overlap
    # --------------------------------

    matching_words = (
        claim_words.intersection(evidence_words)
    )

    keyword_score = (
        len(matching_words) /
        len(claim_words)
    )

    # --------------------------------
    # 3. Related concept matching
    # --------------------------------

    concept_matches = get_concept_matches(
        claim_words,
        evidence_words
    )

    concept_score = min(
        concept_matches / 2,
        1.0
    )

    # --------------------------------
    # 4. TF-IDF similarity
    # --------------------------------

    try:

        vectorizer = TfidfVectorizer(
            stop_words="english"
        )

        matrix = vectorizer.fit_transform([
            claim_clean,
            evidence_clean
        ])

        tfidf_score = cosine_similarity(
            matrix[0:1],
            matrix[1:2]
        )[0][0]

    except ValueError:

        tfidf_score = 0.0

    # --------------------------------
    # 5. Exact phrase gets maximum
    # --------------------------------

    if exact_match:

        return 1.0

    # --------------------------------
    # 6. Combined relevance
    # --------------------------------

    combined_score = (
        0.45 * keyword_score
        +
        0.30 * concept_score
        +
        0.25 * tfidf_score
    )

    # --------------------------------
    # 7. Strong direct match bonus
    # --------------------------------

    if len(matching_words) >= 2:

        combined_score += 0.10

    # --------------------------------
    # 8. Keep between 0 and 1
    # --------------------------------

    combined_score = min(
        float(combined_score),
        1.0
    )

    return round(
        combined_score,
        2
    )
