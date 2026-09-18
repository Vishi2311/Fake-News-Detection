import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {
    "the", "a", "an", "and", "or", "is", "are",
    "was", "were", "to", "of", "in", "on", "for",
    "with", "by", "from", "this", "that",
    "these", "those", "has", "have", "had",
    "will", "would", "could", "should",
    "after", "before", "into", "during",
    "than", "then", "their", "they",
    "them", "its", "it", "as", "at",
    "be", "been", "being", "but", "not",
    "about", "over", "under", "also",
}


# ============================================================
# GENERIC RELATED CONCEPTS
# ============================================================

RELATED_WORDS = {

    "weather": {
        "weather", "forecast", "rain", "rainfall",
        "storm", "storms", "thunderstorm",
        "showers", "heatwave", "temperature",
        "monsoon", "imd", "winds"
    },

    "space": {
        "mission", "missions", "launch", "launched",
        "lander", "landing", "landings",
        "spacecraft", "space", "moon", "lunar",
        "artemis", "isro", "nasa", "satellite",
        "rocket"
    },

    "delhi_region": {
        "delhi", "delhi-ncr", "ncr", "noida",
        "ghaziabad", "gurgaon", "gurugram"
    },

    "cricket": {
        "cricket", "match", "matches", "final",
        "semi-final", "semifinal", "tournament",
        "innings", "batting", "bowling",
        "wicket", "wickets", "runs", "score",
        "player", "team", "teams", "champion",
        "champions", "trophy"
    },

    "politics": {
        "government", "minister", "president",
        "prime", "parliament", "election",
        "elections", "party", "political",
        "politics", "vote", "voting",
        "policy", "cabinet"
    },

    "economy": {
        "economy", "economic", "inflation",
        "gdp", "growth", "market", "markets",
        "rupee", "bank", "banking", "interest",
        "tax", "taxes", "budget", "finance"
    },

    "health": {
        "health", "hospital", "hospitals",
        "doctor", "doctors", "disease",
        "diseases", "virus", "vaccination",
        "vaccine", "treatment", "medical",
        "medicine", "patients"
    },
}


# ============================================================
# IMPORTANT NEWS TERMS
# ============================================================

IMPORTANT_TERMS = {
    "final",
    "winner",
    "won",
    "defeated",
    "defeat",
    "champion",
    "champions",
    "title",
    "tournament",
    "election",
    "elected",
    "appointed",
    "approved",
    "announced",
    "launched",
    "launch",
    "ordered",
    "signed",
    "agreement",
    "agreement",
    "attack",
    "attacked",
    "arrested",
    "arrest",
    "died",
    "death",
    "killed",
    "decision",
    "verdict",
    "ruling",
    "court",
    "government",
    "president",
    "prime",
    "minister",
}


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text):
    """
    Extract useful normalized words.
    """

    if not text:
        return set()

    words = re.findall(
        r"[a-zA-Z0-9-]+",
        str(text).lower()
    )

    return {
        word
        for word in words
        if len(word) > 2
        and word not in STOP_WORDS
    }


# ============================================================
# YEAR EXTRACTION
# ============================================================

def extract_years(text):
    """
    Extract four-digit years such as 2025, 2026, etc.
    """

    if not text:
        return set()

    return set(
        re.findall(
            r"\b(?:19|20)\d{2}\b",
            str(text)
        )
    )


# ============================================================
# NUMBER EXTRACTION
# ============================================================

def extract_numbers(text):
    """
    Extract meaningful numbers.

    Useful for:
    - scores
    - dates
    - quantities
    - years
    """

    if not text:
        return set()

    return set(
        re.findall(
            r"\b\d+(?:\.\d+)?\b",
            str(text)
        )
    )


# ============================================================
# ENTITY-LIKE TERMS
# ============================================================

def extract_entities(text):
    """
    Extract potentially important named entities.

    This is intentionally lightweight and does not require
    a large NLP model.

    Examples:
        India
        ICC
        Champions
        Trophy
        New
        Zealand
    """

    if not text:
        return set()

    words = re.findall(
        r"\b[A-Za-z][A-Za-z0-9-]*\b",
        str(text)
    )

    entities = set()

    for word in words:

        lower_word = word.lower()

        if lower_word in STOP_WORDS:
            continue

        if len(word) <= 2:
            continue

        # Keep capitalized words because they often represent
        # names, organizations, places, teams, etc.
        if word[0].isupper():

            entities.add(
                lower_word
            )

    return entities


# ============================================================
# CONCEPT MATCHING
# ============================================================

def get_concept_matches(
    claim_words,
    evidence_words
):
    """
    Determine how many broad concepts are shared.
    """

    matches = 0

    matched_groups = []

    for group_name, group_words in RELATED_WORDS.items():

        claim_has_group = bool(
            claim_words.intersection(
                group_words
            )
        )

        evidence_has_group = bool(
            evidence_words.intersection(
                group_words
            )
        )

        if (
            claim_has_group
            and evidence_has_group
        ):

            matches += 1

            matched_groups.append(
                group_name
            )

    return (
        matches,
        matched_groups
    )


# ============================================================
# IMPORTANT TERM MATCHING
# ============================================================

def get_important_term_score(
    claim_words,
    evidence_words
):
    """
    Measure overlap of important event/action terms.
    """

    claim_important = (
        claim_words.intersection(
            IMPORTANT_TERMS
        )
    )

    if not claim_important:
        return 0.0

    matched = (
        claim_important.intersection(
            evidence_words
        )
    )

    return (
        len(matched)
        /
        len(claim_important)
    )


# ============================================================
# PHRASE MATCHING
# ============================================================

def get_phrase_overlap(
    claim,
    evidence
):
    """
    Detect multi-word phrases shared between claim
    and evidence.

    Uses bigrams and trigrams.
    """

    claim_tokens = re.findall(
        r"[a-zA-Z0-9-]+",
        claim.lower()
    )

    evidence_tokens = re.findall(
        r"[a-zA-Z0-9-]+",
        evidence.lower()
    )

    if not claim_tokens or not evidence_tokens:
        return 0.0

    claim_phrases = set()

    for n in (2, 3):

        for i in range(
            len(claim_tokens) - n + 1
        ):

            phrase = " ".join(
                claim_tokens[i:i + n]
            )

            claim_phrases.add(
                phrase
            )

    if not claim_phrases:
        return 0.0

    evidence_text = " ".join(
        evidence_tokens
    )

    matched = sum(
        1
        for phrase in claim_phrases
        if phrase in evidence_text
    )

    return (
        matched
        /
        len(claim_phrases)
    )


# ============================================================
# TF-IDF SIMILARITY
# ============================================================

def calculate_tfidf_similarity(
    claim,
    evidence
):
    """
    Calculate cosine similarity between claim
    and evidence.
    """

    try:

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )

        matrix = vectorizer.fit_transform(
            [
                claim,
                evidence
            ]
        )

        return float(
            cosine_similarity(
                matrix[0:1],
                matrix[1:2]
            )[0][0]
        )

    except ValueError:

        return 0.0


# ============================================================
# MAIN RELEVANCE CALCULATOR
# ============================================================

def calculate_relevance(
    claim,
    evidence_title
):
    """
    Calculate relevance between a news claim
    and an evidence title.

    Factors:

    1. Exact phrase match
    2. Keyword overlap
    3. Named-entity overlap
    4. Year match
    5. Important event/action terms
    6. Concept/topic match
    7. Phrase overlap
    8. TF-IDF similarity

    Returns:
        float between 0.0 and 1.0
    """

    if not claim or not evidence_title:
        return 0.0

    claim_clean = (
        str(claim)
        .lower()
        .strip()
    )

    evidence_clean = (
        str(evidence_title)
        .lower()
        .strip()
    )

    claim_words = tokenize(
        claim_clean
    )

    evidence_words = tokenize(
        evidence_clean
    )

    if not claim_words or not evidence_words:
        return 0.0

    # ========================================================
    # 1. EXACT PHRASE MATCH
    # ========================================================

    if claim_clean in evidence_clean:

        return 1.0

    # ========================================================
    # 2. KEYWORD OVERLAP
    # ========================================================

    matching_words = (
        claim_words.intersection(
            evidence_words
        )
    )

    keyword_score = (
        len(matching_words)
        /
        max(len(claim_words), 1)
    )

    # ========================================================
    # 3. ENTITY OVERLAP
    # ========================================================

    claim_entities = extract_entities(
        claim
    )

    evidence_entities = extract_entities(
        evidence_title
    )

    entity_matches = (
        claim_entities.intersection(
            evidence_entities
        )
    )

    if claim_entities:

        entity_score = (
            len(entity_matches)
            /
            len(claim_entities)
        )

    else:

        entity_score = 0.0

    # ========================================================
    # 4. YEAR MATCH
    # ========================================================

    claim_years = extract_years(
        claim
    )

    evidence_years = extract_years(
        evidence_title
    )

    if claim_years:

        year_score = (
            1.0
            if claim_years.intersection(
                evidence_years
            )
            else 0.0
        )

    else:

        year_score = 0.5

    # ========================================================
    # 5. IMPORTANT TERM SCORE
    # ========================================================

    important_score = (
        get_important_term_score(
            claim_words,
            evidence_words
        )
    )

    # ========================================================
    # 6. CONCEPT SCORE
    # ========================================================

    concept_matches, matched_groups = (
        get_concept_matches(
            claim_words,
            evidence_words
        )
    )

    if concept_matches > 0:

        concept_score = min(
            concept_matches / 2,
            1.0
        )

    else:

        concept_score = 0.0

    # ========================================================
    # 7. PHRASE OVERLAP
    # ========================================================

    phrase_score = get_phrase_overlap(
        claim,
        evidence_title
    )

    # ========================================================
    # 8. TF-IDF
    # ========================================================

    tfidf_score = (
        calculate_tfidf_similarity(
            claim_clean,
            evidence_clean
        )
    )

    # ========================================================
    # 9. BASE SCORE
    # ========================================================

    combined_score = (

        0.30 * keyword_score

        +

        0.15 * entity_score

        +

        0.10 * year_score

        +

        0.15 * important_score

        +

        0.10 * concept_score

        +

        0.10 * phrase_score

        +

        0.10 * tfidf_score

    )

    # ========================================================
    # 10. SAME EVENT BONUS
    # ========================================================
    #
    # If:
    #
    # - entities overlap
    # - year matches
    # - topic/concept matches
    #
    # then the evidence is probably about the same event.
    #
    # This is especially important for:
    #
    # India + Champions Trophy + 2025
    #
    # ========================================================

    same_event = (

        len(entity_matches) >= 1

        and

        year_score == 1.0

        and

        concept_score > 0
    )

    if same_event:

        combined_score += 0.12

    # ========================================================
    # 11. STRONG MULTI-WORD MATCH BONUS
    # ========================================================

    if len(matching_words) >= 3:

        combined_score += 0.08

    elif len(matching_words) >= 2:

        combined_score += 0.04

    # ========================================================
    # 12. STRONG EVENT PHRASE BONUS
    # ========================================================

    if phrase_score >= 0.30:

        combined_score += 0.05

    # ========================================================
    # 13. PREVENT FALSE HIGH SCORES
    # ========================================================
    #
    # An article mentioning only "India" should not
    # become highly relevant.
    #
    # ========================================================

    if (
        len(matching_words) <= 1
        and entity_score <= 0.20
        and phrase_score == 0
    ):

        combined_score = min(
            combined_score,
            0.35
        )

    # ========================================================
    # 14. CLAMP
    # ========================================================

    combined_score = max(
        0.0,
        min(
            float(combined_score),
            1.0
        )
    )

    return round(
        combined_score,
        2
    )


# ============================================================
# OPTIONAL DEBUG FUNCTION
# ============================================================

def explain_relevance(
    claim,
    evidence_title
):
    """
    Useful for debugging the scorer.

    Returns the individual components so we can
    understand why a result received its score.
    """

    claim_words = tokenize(
        claim
    )

    evidence_words = tokenize(
        evidence_title
    )

    matching_words = (
        claim_words.intersection(
            evidence_words
        )
    )

    claim_entities = extract_entities(
        claim
    )

    evidence_entities = extract_entities(
        evidence_title
    )

    entity_matches = (
        claim_entities.intersection(
            evidence_entities
        )
    )

    concept_matches, matched_groups = (
        get_concept_matches(
            claim_words,
            evidence_words
        )
    )

    claim_years = extract_years(
        claim
    )

    evidence_years = extract_years(
        evidence_title
    )

    if claim_years:

        year_score = (
            1.0
            if claim_years.intersection(
                evidence_years
            )
            else 0.0
        )

    else:

        year_score = 0.5

    return {
        "relevance": calculate_relevance(
            claim,
            evidence_title
        ),

        "matching_words":
            sorted(matching_words),

        "entity_matches":
            sorted(entity_matches),

        "claim_entities":
            sorted(claim_entities),

        "evidence_entities":
            sorted(evidence_entities),

        "year_match":
            year_score,

        "concept_matches":
            concept_matches,

        "matched_concepts":
            matched_groups,

        "important_term_score":
            get_important_term_score(
                claim_words,
                evidence_words
            ),

        "phrase_score":
            get_phrase_overlap(
                claim,
                evidence_title
            ),

        "tfidf_score":
            round(
                calculate_tfidf_similarity(
                    claim,
                    evidence_title
                ),
                3
            ),
    }