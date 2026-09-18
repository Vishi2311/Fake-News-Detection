import os
import re
import math
import requests
import feedparser

from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup


# ============================================================
# FAKE NEWS DETECTION V2.1
# CLAIM-LEVEL EVIDENCE VERIFICATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

SEARCH_LIMIT = 10
FINAL_EVIDENCE_LIMIT = 5

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/142.0 Safari/537.36"
)


# ============================================================
# TRUSTED DOMAINS
# ============================================================

TRUSTED_DOMAINS = {

    "nasa.gov": 1.00,
    "who.int": 1.00,
    "un.org": 1.00,
    "gov.in": 1.00,
    "india.gov.in": 1.00,
    "pib.gov.in": 1.00,
    "supremecourt.gov": 1.00,
    "icc-cpi.int": 1.00,

    "reuters.com": 0.95,
    "apnews.com": 0.95,
    "bbc.com": 0.90,
    "bbc.co.uk": 0.90,
    "theguardian.com": 0.85,
    "nytimes.com": 0.85,
    "washingtonpost.com": 0.85,

    "thehindu.com": 0.85,
    "indianexpress.com": 0.85,
    "hindustantimes.com": 0.80,
    "indiatoday.in": 0.80,
    "timesofindia.indiatimes.com": 0.75,

    "aljazeera.com": 0.85,
    "cnbc.com": 0.80,
    "bloomberg.com": 0.85,
    "cbc.ca": 0.80,
    "rappler.com": 0.80,
    "theconversation.com": 0.75,

    "olympics.com": 0.90,
    "fifa.com": 1.00,
}


# ============================================================
# PUBLISHER → DOMAIN
# ============================================================

PUBLISHER_DOMAIN_MAP = {

    "reuters": "reuters.com",

    "associated press": "apnews.com",
    "ap news": "apnews.com",

    "bbc": "bbc.com",

    "the hindu": "thehindu.com",
    "indian express": "indianexpress.com",
    "hindustan times": "hindustantimes.com",
    "india today": "indiatoday.in",

    "times of india":
        "timesofindia.indiatimes.com",

    "the guardian": "theguardian.com",
    "new york times": "nytimes.com",
    "washington post": "washingtonpost.com",

    "al jazeera": "aljazeera.com",
    "bloomberg": "bloomberg.com",
    "cnbc": "cnbc.com",

    "cbc": "cbc.ca",
    "rappler": "rappler.com",

    "the conversation":
        "theconversation.com",

    "olympics": "olympics.com",
    "olympics.com": "olympics.com",

    "fifa": "fifa.com",

    "nasa": "nasa.gov",
}


# ============================================================
# BLOCKED DOMAINS
# ============================================================

BLOCKED_DOMAINS = {

    "facebook.com",
    "instagram.com",
    "youtube.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "reddit.com",
    "pinterest.com",
}


AGGREGATOR_DOMAINS = {
    "news.google.com",
}


# ============================================================
# STOPWORDS
# ============================================================

STOPWORDS = {

    "the", "a", "an", "and", "or",
    "but", "if", "then", "than",
    "that", "this", "these",
    "those", "is", "are",
    "was", "were", "be",
    "been", "being", "to",
    "of", "in", "on", "at",
    "for", "from", "by",
    "with", "as", "into",
    "about", "after",
    "before", "during",
    "through", "over",
    "under", "between",
    "has", "have", "had",
    "will", "would",
    "can", "could",
    "may", "might",
    "should", "their",
    "his", "her", "its",
    "they", "them",
    "he", "she",
    "it", "we",
    "you", "i",
    "who", "what",
    "where", "when",
    "why", "how",
    "up", "down",
    "out", "not",
    "no", "than",
}


# ============================================================
# EVENT GROUPS
# ============================================================

EVENT_GROUPS = {

    "sports": {
        "match", "final", "champion",
        "championship", "world cup",
        "tournament", "football",
        "soccer", "cricket",
        "olympics", "goal",
        "goals", "defeat",
        "defeated", "beating",
        "won", "win",
        "victory", "winner"
    },

    "election": {
        "election", "elected",
        "vote", "voting",
        "poll", "president",
        "presidential"
    },

    "death": {
        "death", "dead",
        "died", "killed",
        "killing", "fatal",
        "fatalities"
    },

    "arrest": {
        "arrest", "arrested",
        "detained", "detention",
        "custody"
    },

    "attack": {
        "attack", "attacked",
        "strike", "struck",
        "bombing", "bombed"
    },

    "agreement": {
        "agreement", "deal",
        "accord", "signed",
        "treaty"
    },

    "ban": {
        "ban", "banned",
        "prohibited",
        "prohibition"
    },

    "weather": {
        "rain", "rainfall",
        "flood", "flooding",
        "storm", "typhoon",
        "earthquake",
        "tornado", "hurricane",
        "landslide"
    },

    "economic": {
        "sales", "revenue",
        "economy", "economic",
        "inflation", "spending",
        "growth", "decline"
    },

    "launch": {
        "launch", "launched",
        "launches", "liftoff",
        "mission"
    },

    "release": {
        "release", "released",
        "free", "freed",
        "liberated"
    },

    "build": {
        "build", "built",
        "building", "construct",
        "construction",
        "establish", "established"
    },
}


# ============================================================
# NEGATION / DEBUNKING
# ============================================================

NEGATION_PATTERNS = [

    r"\bno\b",
    r"\bnot\b",
    r"\bdenies\b",
    r"\bdenied\b",
    r"\bfalse\b",
    r"\bfact check\b",
    r"\bfact-check\b",
    r"\bdebunked\b",
    r"\bdebunk\b",
    r"\bmisleading\b",
    r"\bmisrepresents\b",
    r"\bnever\b",
    r"\bdid not\b",
    r"\bdoes not\b",
    r"\bhas not\b",
    r"\bwill not\b",
    r"\bno evidence\b",
    r"\bincorrect\b",
    r"\buntrue\b",
    r"\bhoax\b",
    r"\bfake news\b",
    r"\bfalse claim\b",
]


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(text):

    text = str(text).lower()

    text = re.sub(
        r"https?://\S+",
        " ",
        text
    )

    text = re.sub(
        r"[^a-z0-9\s]",
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
# TOKENS
# ============================================================

def tokens(text):

    words = normalize(
        text
    ).split()

    return [

        word

        for word in words

        if (
            word not in STOPWORDS
            and len(word) > 2
        )
    ]


def important_tokens(text):

    return set(
        tokens(text)
    )


# ============================================================
# NUMBERS
# ============================================================

def extract_numbers(text):

    return set(
        re.findall(
            r"\b(?:19|20)\d{2}\b"
            r"|\b\d+(?:\.\d+)?\b",
            str(text).lower()
        )
    )


def extract_years(text):

    return set(
        re.findall(
            r"\b(?:19|20)\d{2}\b",
            str(text).lower()
        )
    )


# ============================================================
# ENTITIES
# ============================================================

def extract_entities(text):

    original = str(text)

    normalized = normalize(
        original
    )

    found = set()

    capitalized = re.findall(
        r"\b[A-Z][a-z]+"
        r"(?:\s+[A-Z][a-z]+){0,3}\b",
        original
    )

    for entity in capitalized:

        cleaned = normalize(
            entity
        )

        if (
            cleaned
            and len(cleaned) > 2
            and cleaned not in STOPWORDS
        ):

            found.add(cleaned)

    abbreviations = re.findall(
        r"\b[A-Z]{2,}\b",
        original
    )

    for item in abbreviations:

        found.add(
            item.lower()
        )

    important_phrases = [

        "world cup",
        "fifa world cup",
        "prime minister",
        "supreme court",
        "international criminal court",
        "united nations",
        "air india",
        "white house",
        "central government",
        "state government",
    ]

    for phrase in important_phrases:

        if phrase in normalized:

            found.add(
                phrase
            )

    return found


# ============================================================
# EVENT EXTRACTION
# ============================================================

def extract_event_groups(text):

    normalized = normalize(
        text
    )

    events = set()

    for group, keywords in EVENT_GROUPS.items():

        for keyword in keywords:

            if keyword in normalized:

                events.add(
                    group
                )

                break

    return events


# ============================================================
# CLAIM TYPE
# ============================================================

def detect_claim_type(text):

    t = normalize(
        text
    )

    future_phrases = [

        "plans to",
        "plan to",
        "intends to",
        "aims to",
        "proposes to",
        "will build",
        "will launch",
        "will establish",
        "will become",
    ]

    for phrase in future_phrases:

        if phrase in t:

            return "FUTURE_OR_PLAN"

    return "GENERAL_FACT"


# ============================================================
# GOOGLE NEWS SEARCH
# ============================================================

def google_news_search(
    query,
    limit=SEARCH_LIMIT
):

    encoded = quote_plus(
        query
    )

    url = (
        "https://news.google.com/rss/search?"
        f"q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    )

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent":
                    USER_AGENT
            },
            timeout=15
        )

        response.raise_for_status()

        feed = feedparser.parse(
            response.content
        )

        results = []

        for entry in feed.entries[:limit]:

            results.append({

                "title":
                    entry.get(
                        "title",
                        ""
                    ).strip(),

                "link":
                    entry.get(
                        "link",
                        ""
                    ).strip(),

                "summary":
                    entry.get(
                        "summary",
                        ""
                    ).strip(),

                "source":
                    (
                        entry.source.get(
                            "title",
                            ""
                        ).strip()
                        if hasattr(
                            entry,
                            "source"
                        )
                        else ""
                    )
            })

        return results

    except Exception as e:

        print(
            f"Search error: {e}"
        )

        return []


# ============================================================
# DOMAIN
# ============================================================

def get_domain(url):

    try:

        domain = urlparse(
            url
        ).netloc.lower()

        if domain.startswith(
            "www."
        ):

            domain = domain[4:]

        return domain

    except Exception:

        return ""


# ============================================================
# PUBLISHER DOMAIN
# ============================================================

def get_publisher_domain(item):

    source = item.get(
        "source",
        ""
    ).lower().strip()

    title = item.get(
        "title",
        ""
    ).lower().strip()

    link = item.get(
        "link",
        ""
    )

    for publisher, domain in (
        PUBLISHER_DOMAIN_MAP.items()
    ):

        if publisher in source:

            return domain

    for publisher, domain in (
        PUBLISHER_DOMAIN_MAP.items()
    ):

        if publisher in title:

            return domain

    domain = get_domain(
        link
    )

    if (
        domain
        and domain not in AGGREGATOR_DOMAINS
    ):

        return domain

    return ""


# ============================================================
# TRUST SCORE
# ============================================================

def trusted_score(domain):

    if not domain:

        return 0.0

    for trusted_domain, score in (
        TRUSTED_DOMAINS.items()
    ):

        if (

            domain == trusted_domain

            or domain.endswith(
                "." + trusted_domain
            )
        ):

            return score

    return 0.0


# ============================================================
# BLOCKED DOMAIN
# ============================================================

def is_blocked_domain(domain):

    if not domain:

        return False

    return any(

        domain == blocked

        or domain.endswith(
            "." + blocked
        )

        for blocked in BLOCKED_DOMAINS
    )


# ============================================================
# HTML CLEANING
# ============================================================

def clean_html(text):

    soup = BeautifulSoup(
        text,
        "html.parser"
    )

    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "footer",
        "nav"
    ]):

        tag.decompose()

    return soup.get_text(
        " ",
        strip=True
    )


# ============================================================
# ARTICLE RETRIEVAL
# ============================================================

def retrieve_article(url):

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent":
                    USER_AGENT
            },
            timeout=12
        )

        if response.status_code != 200:

            return ""

        domain = get_domain(
            response.url
        )

        if is_blocked_domain(
            domain
        ):

            return ""

        text = clean_html(
            response.text
        )

        if len(text) < 300:

            return ""

        return text[:40000]

    except Exception:

        return ""


# ============================================================
# OVERLAP
# ============================================================

def overlap_score(
    claim_words,
    evidence_words
):

    if not claim_words:

        return 0.0

    return (

        len(
            claim_words
            & evidence_words
        )

        /

        len(
            claim_words
        )
    )


def entity_overlap(
    claim_entities,
    evidence_entities
):

    if not claim_entities:

        return 0.0

    return (

        len(
            claim_entities
            & evidence_entities
        )

        /

        len(
            claim_entities
        )
    )


def event_overlap(
    claim_events,
    evidence_events
):

    if not claim_events:

        return 0.0

    return (

        len(
            claim_events
            & evidence_events
        )

        /

        len(
            claim_events
        )
    )


# ============================================================
# NEGATION
# ============================================================

def has_negation(text):

    normalized = normalize(
        text
    )

    return any(

        re.search(
            pattern,
            normalized
        )

        for pattern
        in NEGATION_PATTERNS
    )


# ============================================================
# OUTCOME DETECTION
# ============================================================

def detect_outcome(text):

    t = normalize(
        text
    )

    outcomes = {

        "win": [
            "won",
            "wins",
            "win",
            "victory",
            "defeated",
            "beat",
            "beats",
            "champion",
            "champions",
        ],

        "loss": [
            "lost",
            "loss",
            "defeated by",
            "eliminated",
            "runner up",
        ],

        "death": [
            "died",
            "dead",
            "killed",
            "death",
        ],

        "arrest": [
            "arrested",
            "detained",
            "taken into custody",
        ],
    }

    found = set()

    for outcome, words in outcomes.items():

        if any(
            word in t
            for word in words
        ):

            found.add(
                outcome
            )

    return found


# ============================================================
# CLAIM RELATIONSHIP
# ============================================================

def detect_relationship(
    claim,
    evidence_text
):

    claim_words = important_tokens(
        claim
    )

    evidence_words = important_tokens(
        evidence_text
    )

    claim_entities = extract_entities(
        claim
    )

    evidence_entities = extract_entities(
        evidence_text
    )

    claim_events = extract_event_groups(
        claim
    )

    evidence_events = extract_event_groups(
        evidence_text
    )

    claim_numbers = extract_numbers(
        claim
    )

    evidence_numbers = extract_numbers(
        evidence_text
    )

    claim_years = extract_years(
        claim
    )

    evidence_years = extract_years(
        evidence_text
    )

    word_score = overlap_score(
        claim_words,
        evidence_words
    )

    entity_score = entity_overlap(
        claim_entities,
        evidence_entities
    )

    event_score = event_overlap(
        claim_events,
        evidence_events
    )

    title_match = word_score

    number_match = 1.0

    if claim_numbers:

        number_match = (

            1.0

            if claim_numbers
            & evidence_numbers

            else 0.0
        )

    year_match = 1.0

    if claim_years:

        year_match = (

            1.0

            if claim_years
            & evidence_years

            else 0.0
        )

    claim_outcomes = detect_outcome(
        claim
    )

    evidence_outcomes = detect_outcome(
        evidence_text
    )

    outcome_match = (

        1.0

        if (
            not claim_outcomes
            or claim_outcomes
            & evidence_outcomes
        )

        else 0.0
    )

    negated = has_negation(
        evidence_text
    )

    # ========================================================
    # VERY STRONG NEGATIVE SIGNAL
    # ========================================================

    explicit_debunk = (

        negated

        and entity_score >= 0.30

        and (
            word_score >= 0.20
            or event_score >= 0.50
        )
    )

    if explicit_debunk:

        return {

            "relationship":
                "DIRECT_CONTRADICTION",

            "supporting": False,
            "contradicting": True,

            "claim_overlap":
                word_score,

            "entity_overlap":
                entity_score,

            "event_overlap":
                event_score,

            "number_match":
                number_match,

            "year_match":
                year_match,

            "outcome_match":
                outcome_match,

            "title_match":
                title_match,
        }

    # ========================================================
    # WRONG OUTCOME
    # ========================================================

    if (

        claim_outcomes

        and evidence_outcomes

        and not (
            claim_outcomes
            & evidence_outcomes
        )

        and entity_score >= 0.40

        and event_score >= 0.50

    ):

        return {

            "relationship":
                "OUTCOME_CONTRADICTION",

            "supporting": False,
            "contradicting": True,

            "claim_overlap":
                word_score,

            "entity_overlap":
                entity_score,

            "event_overlap":
                event_score,

            "number_match":
                number_match,

            "year_match":
                year_match,

            "outcome_match":
                0.0,

            "title_match":
                title_match,
        }

    # ========================================================
    # DIRECT SUPPORT
    # ========================================================

    direct_support = (

        word_score >= 0.35

        and entity_score >= 0.30

        and event_score >= 0.40

        and number_match >= 0.5

        and year_match >= 0.5

        and outcome_match >= 0.5
    )

    if direct_support:

        return {

            "relationship":
                "DIRECT_SUPPORT",

            "supporting": True,
            "contradicting": False,

            "claim_overlap":
                word_score,

            "entity_overlap":
                entity_score,

            "event_overlap":
                event_score,

            "number_match":
                number_match,

            "year_match":
                year_match,

            "outcome_match":
                outcome_match,

            "title_match":
                title_match,
        }

    # ========================================================
    # STRONG EVENT MATCH
    # ========================================================

    strong_event = (

        event_score >= 0.50

        and entity_score >= 0.25

        and word_score >= 0.25

        and outcome_match >= 0.5

        and year_match >= 0.5
    )

    if strong_event:

        return {

            "relationship":
                "STRONG_EVENT_MATCH",

            "supporting": True,
            "contradicting": False,

            "claim_overlap":
                word_score,

            "entity_overlap":
                entity_score,

            "event_overlap":
                event_score,

            "number_match":
                number_match,

            "year_match":
                year_match,

            "outcome_match":
                outcome_match,

            "title_match":
                title_match,
        }

    # ========================================================
    # RELATED ONLY
    # ========================================================

    if (

        entity_score >= 0.25

        or event_score >= 0.40

    ) and word_score >= 0.12:

        return {

            "relationship":
                "RELATED_ONLY",

            "supporting": False,
            "contradicting": False,

            "claim_overlap":
                word_score,

            "entity_overlap":
                entity_score,

            "event_overlap":
                event_score,

            "number_match":
                number_match,

            "year_match":
                year_match,

            "outcome_match":
                outcome_match,

            "title_match":
                title_match,
        }

    # ========================================================
    # IRRELEVANT
    # ========================================================

    return {

        "relationship":
            "IRRELEVANT",

        "supporting": False,
        "contradicting": False,

        "claim_overlap":
            word_score,

        "entity_overlap":
            entity_score,

        "event_overlap":
            event_score,

        "number_match":
            number_match,

        "year_match":
            year_match,

        "outcome_match":
            outcome_match,

        "title_match":
            title_match,
    }


# ============================================================
# EVIDENCE QUALITY
# ============================================================

def evidence_quality(
    relevance,
    trust,
    article_content,
    relationship
):

    relationship_bonus = {

        "DIRECT_SUPPORT":
            0.25,

        "STRONG_EVENT_MATCH":
            0.12,

        "DIRECT_CONTRADICTION":
            0.30,

        "OUTCOME_CONTRADICTION":
            0.30,

        "RELATED_ONLY":
            -0.15,

        "IRRELEVANT":
            -0.35,
    }

    bonus = relationship_bonus.get(
        relationship,
        0.0
    )

    quality = (

        relevance * 0.25

        + trust * 0.40

        + article_content * 0.15

        + 0.20

        + bonus
    )

    return max(
        0.0,
        min(
            1.0,
            quality
        )
    )


# ============================================================
# SEARCH QUERY GENERATION
# ============================================================

def build_queries(
    headline,
    article
):

    queries = []

    headline = headline.strip()

    article = article.strip()

    if headline:

        queries.append(
            f'"{headline}"'
        )

        queries.append(
            f'"{headline}" fact check'
        )

        queries.append(
            headline
        )

    entities = list(
        extract_entities(
            headline
            + " "
            + article
        )
    )

    if entities:

        queries.append(
            " ".join(
                entities[:5]
            )
        )

    headline_words = [

        word

        for word
        in tokens(headline)

        if len(word) >= 4
    ]

    if headline_words:

        queries.append(
            " ".join(
                headline_words[:8]
            )
        )

    article_words = [

        word

        for word
        in tokens(article)

        if len(word) >= 5
    ]

    if article_words:

        queries.append(
            " ".join(
                article_words[:8]
            )
        )

    return list(
        dict.fromkeys(
            q.strip()
            for q in queries
            if q.strip()
        )
    )


# ============================================================
# TITLE SIMILARITY
# ============================================================

def title_similarity(
    headline,
    result_title
):

    return overlap_score(

        important_tokens(
            headline
        ),

        important_tokens(
            result_title
        )
    )


# ============================================================
# COLLECT EVIDENCE
# ============================================================

def collect_evidence(
    headline,
    article
):

    claim = (
        headline.strip()
        + " "
        + article.strip()
    )

    queries = build_queries(
        headline,
        article
    )

    raw_results = []

    for query in queries:

        raw_results.extend(
            google_news_search(
                query
            )
        )

    # ========================================================
    # DEDUPLICATE
    # ========================================================

    unique = {}

    for item in raw_results:

        title = item.get(
            "title",
            ""
        ).strip()

        normalized = normalize(
            title
        )

        if normalized:

            unique[
                normalized
            ] = item

    evidence = []

    # ========================================================
    # PROCESS
    # ========================================================

    for item in unique.values():

        title = item.get(
            "title",
            ""
        )

        summary = clean_html(
            item.get(
                "summary",
                ""
            )
        )

        link = item.get(
            "link",
            ""
        )

        combined = (
            title
            + " "
            + summary
        )

        relevance = overlap_score(

            important_tokens(
                claim
            ),

            important_tokens(
                combined
            )
        )

        title_match = title_similarity(
            headline,
            title
        )

        if (

            relevance < 0.08

            and title_match < 0.15
        ):

            continue

        domain = get_publisher_domain(
            item
        )

        if is_blocked_domain(
            domain
        ):

            continue

        article_content = retrieve_article(
            link
        )

        content = (

            article_content

            if article_content

            else summary
        )

        relationship = detect_relationship(

            claim,

            title
            + " "
            + content
        )

        trust = trusted_score(
            domain
        )

        content_score = (

            1.0

            if article_content

            else 0.0
        )

        quality = evidence_quality(

            relevance,

            trust,

            content_score,

            relationship[
                "relationship"
            ]
        )

        if title_match >= 0.80:

            quality = min(
                1.0,
                quality + 0.10
            )

        evidence.append({

            "source":
                domain
                or item.get(
                    "source",
                    "Unknown"
                ),

            "publisher":
                item.get(
                    "source",
                    "Unknown"
                ),

            "title":
                title,

            "link":
                link,

            "type":
                (
                    "ARTICLE_CONTENT"
                    if article_content
                    else "RSS_SUMMARY"
                ),

            "relevance":
                relevance,

            "title_match":
                title_match,

            "claim_overlap":
                relationship[
                    "claim_overlap"
                ],

            "entity_overlap":
                relationship[
                    "entity_overlap"
                ],

            "event_overlap":
                relationship[
                    "event_overlap"
                ],

            "number_match":
                relationship[
                    "number_match"
                ],

            "year_match":
                relationship[
                    "year_match"
                ],

            "outcome_match":
                relationship[
                    "outcome_match"
                ],

            "quality":
                quality,

            "trusted":
                trust >= 0.70,

            "trust_score":
                trust,

            "relationship":
                relationship[
                    "relationship"
                ],

            "supporting":
                relationship[
                    "supporting"
                ],

            "contradicting":
                relationship[
                    "contradicting"
                ],
        })

    # ========================================================
    # RANK
    # ========================================================

    evidence.sort(

        key=lambda x: (

            int(
                x["contradicting"]
            ),

            int(
                x["supporting"]
            ),

            int(
                x["trusted"]
            ),

            x["quality"],

            x["title_match"],

        ),

        reverse=True
    )

    # ========================================================
    # DIVERSITY
    # ========================================================

    selected = []

    domains = set()

    for item in evidence:

        domain = item[
            "source"
        ]

        if (

            domain

            and domain in domains
        ):

            continue

        selected.append(
            item
        )

        if domain:

            domains.add(
                domain
            )

        if len(
            selected
        ) >= FINAL_EVIDENCE_LIMIT:

            break

    return selected


# ============================================================
# FINAL EVIDENCE
# ============================================================

def calculate_final_evidence(
    evidence
):

    if not evidence:

        return {

            "assessment":
                "INCONCLUSIVE",

            "score":
                0.0,

            "level":
                "WEAK",

            "strong_supporting":
                0,

            "strong_contradicting":
                0,

            "trusted_supporting":
                0,

            "trusted_contradicting":
                0,
        }

    supporting = [

        e

        for e in evidence

        if e["supporting"]
    ]

    contradicting = [

        e

        for e in evidence

        if e["contradicting"]
    ]

    strong_supporting = [

        e

        for e in supporting

        if e["quality"] >= 0.55
    ]

    strong_contradicting = [

        e

        for e in contradicting

        if e["quality"] >= 0.55
    ]

    trusted_supporting = [

        e

        for e in supporting

        if e["trusted"]
    ]

    trusted_contradicting = [

        e

        for e in contradicting

        if e["trusted"]
    ]

    # ========================================================
    # STRENGTH
    # ========================================================

    def strength(e):

        relationship = max(

            e["claim_overlap"],

            e["entity_overlap"]
            * max(
                e["event_overlap"],
                0.50
            ),

            e["title_match"]
        )

        precision = (

            1.0

            if e[
                "number_match"
            ] >= 0.5

            else 0.60
        )

        return (

            e["quality"]

            * relationship

            * precision
        )

    support_strength = min(

        1.0,

        sum(
            strength(e)
            for e in supporting
        )
    )

    contradiction_strength = min(

        1.0,

        sum(
            strength(e)
            for e in contradicting
        )
    )

    # ========================================================
    # CONTRADICTION HAS PRIORITY
    # ========================================================

    if (

        trusted_contradicting

        and contradiction_strength >= 0.25
    ):

        assessment = "CONTRADICTED"

        score = min(

            1.0,

            0.65
            + contradiction_strength
            * 0.35
        )

    elif (

        len(
            strong_contradicting
        ) >= 2

        and contradiction_strength >= 0.35
    ):

        assessment = "CONTRADICTED"

        score = min(

            1.0,

            0.60
            + contradiction_strength
            * 0.40
        )

    # ========================================================
    # SUPPORT
    # ========================================================

    elif (

        len(
            trusted_supporting
        ) >= 2

        and support_strength >= 0.30
    ):

        assessment = "SUPPORTED"

        score = min(

            1.0,

            0.60
            + support_strength
            * 0.40
        )

    elif (

        len(
            strong_supporting
        ) >= 3

        and support_strength >= 0.45
    ):

        assessment = "SUPPORTED"

        score = min(

            1.0,

            0.55
            + support_strength
            * 0.45
        )

    else:

        assessment = "INCONCLUSIVE"

        score = 0.0

    # ========================================================
    # LEVEL
    # ========================================================

    if score >= 0.75:

        level = "STRONG"

    elif score >= 0.50:

        level = "MODERATE"

    else:

        level = "WEAK"

    return {

        "assessment":
            assessment,

        "score":
            score,

        "level":
            level,

        "strong_supporting":
            len(
                strong_supporting
            ),

        "strong_contradicting":
            len(
                strong_contradicting
            ),

        "trusted_supporting":
            len(
                trusted_supporting
            ),

        "trusted_contradicting":
            len(
                trusted_contradicting
            ),
    }


# ============================================================
# FINAL DECISION
# ============================================================

def calculate_final_decision(
    ml_label,
    ml_confidence,
    evidence_result
):

    assessment = evidence_result[
        "assessment"
    ]

    evidence_score = evidence_result[
        "score"
    ]

    # ========================================================
    # STRONG CONTRADICTION
    # ========================================================

    if assessment == "CONTRADICTED":

        final_confidence = (

            evidence_score * 0.80

            + ml_confidence * 0.20
        )

        return (

            "FAKE",

            min(
                0.99,
                final_confidence
            )
        )

    # ========================================================
    # STRONG SUPPORT
    # ========================================================

    if assessment == "SUPPORTED":

        final_confidence = (

            evidence_score * 0.80

            + ml_confidence * 0.20
        )

        return (

            "REAL",

            min(
                0.99,
                final_confidence
            )
        )

    # ========================================================
    # INCONCLUSIVE
    # ========================================================

    return (

        "NEEDS VERIFICATION",

        min(
            0.75,
            ml_confidence * 0.55
        )
    )