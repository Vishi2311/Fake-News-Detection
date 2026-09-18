import os
import re
import math
import joblib
import requests
import feedparser

from urllib.parse import quote_plus, urlparse, parse_qs, unquote
from bs4 import BeautifulSoup

# ============================================================
# V2.1 FULL NEWS VERIFICATION PIPELINE
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# ============================================================
# MODEL
# ============================================================

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "v2",
    "v2_calibrated_fake_news_model.pkl"
)

VECTORIZER_PATH = os.path.join(
    BASE_DIR,
    "models",
    "v2",
    "v2_tfidf_vectorizer.pkl"
)

# ============================================================
# CONFIGURATION
# ============================================================

SEARCH_LIMIT = 10
FINAL_EVIDENCE_LIMIT = 5

REQUEST_TIMEOUT = 15
ARTICLE_MAX_LENGTH = 30000

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/142.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ============================================================
# TRUSTED SOURCES
# ============================================================

TRUSTED_DOMAINS = {

    # Government / International
    "nasa.gov": 1.00,
    "who.int": 1.00,
    "un.org": 1.00,
    "gov.in": 1.00,
    "india.gov.in": 1.00,
    "pib.gov.in": 1.00,
    "supremecourt.gov": 1.00,
    "icc-cpi.int": 1.00,

    # Major international news
    "reuters.com": 0.95,
    "apnews.com": 0.95,
    "bbc.com": 0.90,
    "bbc.co.uk": 0.90,
    "theguardian.com": 0.85,
    "nytimes.com": 0.85,
    "washingtonpost.com": 0.85,

    # Indian news
    "thehindu.com": 0.85,
    "indianexpress.com": 0.85,
    "hindustantimes.com": 0.80,
    "indiatoday.in": 0.80,
    "timesofindia.indiatimes.com": 0.75,

    # Other established sources
    "rappler.com": 0.80,
    "cbc.ca": 0.80,
    "cnbc.com": 0.80,
    "aljazeera.com": 0.85,
    "bloomberg.com": 0.85,
    "theconversation.com": 0.75,
}

# ============================================================
# PUBLISHER -> DOMAIN
# ============================================================

PUBLISHER_DOMAIN_MAP = {

    "nasa": "nasa.gov",

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

    "the conversation":
        "theconversation.com",

    "rappler": "rappler.com",

    "cbc": "cbc.ca",
}

# ============================================================
# STOPWORDS
# ============================================================

STOPWORDS = {
    "the", "a", "an", "and", "or", "but",
    "if", "then", "than", "that", "this",
    "these", "those", "is", "are", "was",
    "were", "be", "been", "being", "to",
    "of", "in", "on", "at", "for", "from",
    "by", "with", "as", "into", "about",
    "after", "before", "during", "through",
    "over", "under", "between", "has",
    "have", "had", "will", "would", "can",
    "could", "may", "might", "should",
    "their", "his", "her", "its", "they",
    "them", "he", "she", "it", "we",
    "you", "i", "who", "what", "where",
    "when", "why", "how", "up", "down",
    "out", "not", "no"
}

# ============================================================
# KNOWN ENTITIES
# ============================================================

KNOWN_ENTITIES = {
    "nasa",
    "artemis",
    "artemis ii",
    "moon",
    "mars",
    "chiba",
    "tokyo",
    "narita",
    "india",
    "china",
    "russia",
    "ukraine",
    "israel",
    "palestine",
    "iran",
    "pakistan",
    "japan",
    "philippines",

    "donald trump",
    "trump",

    "duterte",
    "rodrigo duterte",

    "international criminal court",
    "icc",

    "united nations",
    "un",

    "america",
    "united states",
    "us",

    "joe biden",

    "elon musk",
    "spacex",

    "barack obama",

    "air india",
}

# ============================================================
# EVENT GROUPS
# ============================================================

EVENT_GROUPS = {

    "launch": {
        "launch",
        "launched",
        "launches",
        "liftoff",
        "mission",
    },

    "release": {
        "release",
        "released",
        "free",
        "freed",
        "liberated",
    },

    "arrest": {
        "arrest",
        "arrested",
        "detained",
        "detention",
        "custody",
    },

    "announce": {
        "announce",
        "announced",
        "announcement",
        "plan",
        "plans",
        "planned",
        "proposal",
        "proposed",
    },

    "build": {
        "build",
        "built",
        "building",
        "construct",
        "construction",
        "establish",
        "established",
    },

    "death": {
        "death",
        "dead",
        "died",
        "killed",
        "killing",
        "fatal",
        "fatalities",
    },

    "election": {
        "election",
        "elected",
        "vote",
        "voting",
        "poll",
        "president",
    },

    "ban": {
        "ban",
        "banned",
        "prohibited",
        "prohibition",
    },

    "attack": {
        "attack",
        "attacked",
        "strike",
        "struck",
        "bombing",
        "bombed",
    },

    "agreement": {
        "agreement",
        "deal",
        "accord",
        "signed",
        "treaty",
    },

    "weather_disaster": {
        "rain",
        "rains",
        "rainfall",
        "flood",
        "floods",
        "flooded",
        "flooding",
        "storm",
        "storms",
        "typhoon",
        "earthquake",
        "earthquakes",
        "tornado",
        "tornadoes",
        "hurricane",
        "hurricanes",
        "landslide",
        "landslides",
    },

    "flight": {
        "flight",
        "aircraft",
        "airplane",
        "plane",
        "aviation",
        "landing",
        "landed",
        "carrier",
        "carriers",
        "catapult",
        "catapults",
    },

    "economic": {
        "sales",
        "revenue",
        "economy",
        "economic",
        "inflation",
        "spending",
        "growth",
        "decline",
    },
}

# ============================================================
# TEXT NORMALIZATION
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


def tokens(text):

    words = normalize(text).split()

    return [
        word
        for word in words
        if word not in STOPWORDS
        and len(word) > 2
    ]


def important_tokens(text):

    return set(tokens(text))


# ============================================================
# NUMBERS / YEARS
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
# ENTITY EXTRACTION
# ============================================================

def extract_entities(text):

    text_lower = normalize(text)

    found = set()

    for entity in KNOWN_ENTITIES:

        pattern = (
            r"\b"
            + re.escape(entity)
            + r"\b"
        )

        if re.search(
            pattern,
            text_lower
        ):
            found.add(entity)

    return found


# ============================================================
# EVENT EXTRACTION
# ============================================================

def extract_event_groups(text):

    words = set(
        tokens(text)
    )

    events = set()

    for group, keywords in EVENT_GROUPS.items():

        if words.intersection(
            keywords
        ):
            events.add(group)

    return events


# ============================================================
# CLAIM TYPE
# ============================================================

def detect_claim_type(text):

    t = normalize(text)

    future_phrases = [

        "announced plans",
        "has announced plans",
        "announces plans",
        "plans to",
        "plan to",
        "intends to",
        "aims to",
        "proposes to",
        "will build",
        "will launch",
        "will establish",
    ]

    for phrase in future_phrases:

        if phrase in t:
            return "FUTURE_OR_PLAN"

    future_words = {
        "will",
        "plans",
        "plan",
        "intends",
        "aims",
        "expects",
        "proposes",
    }

    words = set(
        t.split()
    )

    if words.intersection(
        future_words
    ):
        return "FUTURE_OR_PLAN"

    past_words = {
        "launched",
        "arrested",
        "released",
        "signed",
        "announced",
        "built",
        "killed",
        "died",
        "approved",
        "flooded",
        "landed",
        "ordered",
    }

    if words.intersection(
        past_words
    ):
        return "PAST_EVENT"

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
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        feed = feedparser.parse(
            response.content
        )

        results = []

        for entry in feed.entries[:limit]:

            title = entry.get(
                "title",
                ""
            ).strip()

            link = entry.get(
                "link",
                ""
            ).strip()

            summary = entry.get(
                "summary",
                ""
            ).strip()

            source_name = ""

            if hasattr(
                entry,
                "source"
            ):

                source_name = (
                    entry.source.get(
                        "title",
                        ""
                    )
                    .strip()
                )

            if not source_name:

                source_name = "Unknown"

            results.append({

                "title": title,

                "link": link,

                "summary": summary,

                "source": source_name,
            })

        return results

    except Exception as e:

        print(
            f"Evidence search error: {e}"
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

    source_name = (
        item.get(
            "source",
            ""
        )
        .lower()
        .strip()
    )

    title = (
        item.get(
            "title",
            ""
        )
        .lower()
        .strip()
    )

    link = (
        item.get(
            "link",
            ""
        )
        .strip()
    )

    # --------------------------------------------------------
    # 1. Known publisher
    # --------------------------------------------------------

    for name, domain in (
        PUBLISHER_DOMAIN_MAP.items()
    ):

        if name in source_name:

            return domain

    # --------------------------------------------------------
    # 2. Publisher in title
    # --------------------------------------------------------

    for name, domain in (
        PUBLISHER_DOMAIN_MAP.items()
    ):

        if (
            f" - {name}" in title
            or f" | {name}" in title
            or title.endswith(
                f" - {name}"
            )
        ):

            return domain

    # --------------------------------------------------------
    # 3. URL domain
    # --------------------------------------------------------

    domain = get_domain(
        link
    )

    if (
        domain
        and domain != "news.google.com"
    ):

        return domain

    # --------------------------------------------------------
    # 4. Publisher itself may be domain
    # --------------------------------------------------------

    cleaned_source = (
        source_name
        .replace(
            "www.",
            ""
        )
        .strip()
    )

    if re.match(
        r"^[a-z0-9.-]+\.[a-z]{2,}$",
        cleaned_source
    ):

        return cleaned_source

    return ""


# ============================================================
# TRUST
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
        "nav",
        "header",
        "aside",
        "form",
    ]):

        tag.decompose()

    return soup.get_text(
        " ",
        strip=True
    )


# ============================================================
# ARTICLE TEXT EXTRACTION
# ============================================================

def extract_article_text(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # Remove obvious non-content elements
    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "footer",
        "nav",
        "header",
        "aside",
        "form",
        "iframe",
    ]):

        tag.decompose()

    # --------------------------------------------------------
    # Prefer article tag
    # --------------------------------------------------------

    article = soup.find(
        "article"
    )

    if article:

        text = article.get_text(
            " ",
            strip=True
        )

        if len(text) >= 500:

            return text

    # --------------------------------------------------------
    # Try common article containers
    # --------------------------------------------------------

    candidates = []

    selectors = [
        "[class*='article-body']",
        "[class*='article-content']",
        "[class*='story-body']",
        "[class*='story-content']",
        "[class*='entry-content']",
        "[class*='post-content']",
        "[class*='article__body']",
        "[class*='article__content']",
    ]

    for selector in selectors:

        try:

            elements = soup.select(
                selector
            )

            for element in elements:

                text = element.get_text(
                    " ",
                    strip=True
                )

                if len(text) >= 300:

                    candidates.append(
                        text
                    )

        except Exception:

            continue

    if candidates:

        return max(
            candidates,
            key=len
        )

    # --------------------------------------------------------
    # Fallback: paragraphs
    # --------------------------------------------------------

    paragraphs = []

    for p in soup.find_all(
        "p"
    ):

        text = p.get_text(
            " ",
            strip=True
        )

        if len(text) >= 40:

            paragraphs.append(
                text
            )

    if paragraphs:

        return " ".join(
            paragraphs
        )

    # --------------------------------------------------------
    # Last fallback
    # --------------------------------------------------------

    return soup.get_text(
        " ",
        strip=True
    )


# ============================================================
# ARTICLE RETRIEVAL
# ============================================================

def retrieve_article(url):

    if not url:

        return ""

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )

        if response.status_code != 200:

            return ""

        content_type = (
            response.headers
            .get(
                "Content-Type",
                ""
            )
            .lower()
        )

        if (
            content_type
            and "html" not in content_type
        ):

            return ""

        text = extract_article_text(
            response.text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        if len(text) < 200:

            return ""

        return text[
            :ARTICLE_MAX_LENGTH
        ]

    except Exception:

        return ""


# ============================================================
# ARTICLE RETRIEVAL THROUGH SEARCH
# ============================================================

def retrieve_publisher_article(
    item,
    publisher_domain
):

    # First try the RSS URL
    article = retrieve_article(
        item.get(
            "link",
            ""
        )
    )

    if article:

        return article

    # --------------------------------------------------------
    # If RSS link cannot be opened, search publisher directly
    # --------------------------------------------------------

    title = item.get(
        "title",
        ""
    )

    if not publisher_domain:

        return ""

    search_query = (
        f"{title} "
        f"site:{publisher_domain}"
    )

    results = google_news_search(
        search_query,
        limit=5
    )

    for result in results:

        result_domain = (
            get_publisher_domain(
                result
            )
        )

        if (
            result_domain
            and result_domain
            == publisher_domain
        ):

            article = retrieve_article(
                result.get(
                    "link",
                    ""
                )
            )

            if article:

                return article

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

    intersection = (
        claim_words.intersection(
            evidence_words
        )
    )

    return (
        len(intersection)
        / len(claim_words)
    )


def entity_overlap(
    claim_entities,
    evidence_entities
):

    if not claim_entities:

        return 0.0

    return (
        len(
            claim_entities.intersection(
                evidence_entities
            )
        )
        /
        len(claim_entities)
    )


def event_overlap(
    claim_events,
    evidence_events
):

    if not claim_events:

        return 0.0

    return (
        len(
            claim_events.intersection(
                evidence_events
            )
        )
        /
        len(claim_events)
    )


# ============================================================
# NEGATION
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
]


def has_negation(text):

    text = normalize(
        text
    )

    return any(
        re.search(
            pattern,
            text
        )
        for pattern in NEGATION_PATTERNS
    )


# ============================================================
# RELATIONSHIP
# ============================================================

def detect_relationship(
    claim,
    evidence_text,
    claim_type
):

    claim_words = important_tokens(
        claim
    )

    evidence_words = important_tokens(
        evidence_text
    )

    entities_claim = extract_entities(
        claim
    )

    entities_evidence = extract_entities(
        evidence_text
    )

    events_claim = extract_event_groups(
        claim
    )

    events_evidence = extract_event_groups(
        evidence_text
    )

    word_score = overlap_score(
        claim_words,
        evidence_words
    )

    entity_score = entity_overlap(
        entities_claim,
        entities_evidence
    )

    event_score = event_overlap(
        events_claim,
        events_evidence
    )

    years_claim = extract_years(
        claim
    )

    years_evidence = extract_years(
        evidence_text
    )

    year_match = 1.0

    if years_claim:

        year_match = (
            1.0
            if years_claim.intersection(
                years_evidence
            )
            else 0.0
        )

    negated = has_negation(
        evidence_text
    )

    # ========================================================
    # CONTRADICTION
    # ========================================================

    explicit_contradiction = (

        negated

        and (

            entity_score >= 0.40

            or event_score >= 0.60
        )

        and word_score >= 0.25
    )

    if explicit_contradiction:

        return {

            "relationship":
                "DIRECT_CONTRADICTION",

            "supporting":
                False,

            "contradicting":
                True,

            "word_score":
                word_score,

            "entity_score":
                entity_score,

            "event_score":
                event_score,

            "year_match":
                year_match,
        }

    # ========================================================
    # DIRECT SUPPORT
    # ========================================================

    direct_match = (

        (

            entity_score >= 0.60

            or event_score >= 0.75
        )

        and word_score >= 0.35

        and (

            year_match >= 0.5

            or not years_claim
        )
    )

    if direct_match:

        return {

            "relationship":
                "DIRECT_SUPPORT",

            "supporting":
                True,

            "contradicting":
                False,

            "word_score":
                word_score,

            "entity_score":
                entity_score,

            "event_score":
                event_score,

            "year_match":
                year_match,
        }

    # ========================================================
    # STRONG EVENT MATCH
    # ========================================================

    strong_event_match = (

        (

            entity_score >= 0.40

            or event_score >= 0.75
        )

        and event_score >= 0.75

        and word_score >= 0.25

        and (

            year_match >= 0.5

            or not years_claim
        )
    )

    if strong_event_match:

        return {

            "relationship":
                "STRONG_EVENT_MATCH",

            "supporting":
                True,

            "contradicting":
                False,

            "word_score":
                word_score,

            "entity_score":
                entity_score,

            "event_score":
                event_score,

            "year_match":
                year_match,
        }

    # ========================================================
    # FUTURE / PLAN PROTECTION
    # ========================================================

    if claim_type == "FUTURE_OR_PLAN":

        if (
            years_claim
            and not years_claim.intersection(
                years_evidence
            )
        ):

            return {

                "relationship":
                    "RELATED_ONLY",

                "supporting":
                    False,

                "contradicting":
                    False,

                "word_score":
                    word_score,

                "entity_score":
                    entity_score,

                "event_score":
                    event_score,

                "year_match":
                    0.0,
            }

        if (
            entity_score < 0.40
            and event_score < 0.60
        ):

            return {

                "relationship":
                    "RELATED_ONLY",

                "supporting":
                    False,

                "contradicting":
                    False,

                "word_score":
                    word_score,

                "entity_score":
                    entity_score,

                "event_score":
                    event_score,

                "year_match":
                    year_match,
            }

    # ========================================================
    # RELATED
    # ========================================================

    if (

        (

            entity_score >= 0.40

            or event_score >= 0.50
        )

        and word_score >= 0.20
    ):

        return {

            "relationship":
                "RELATED_ONLY",

            "supporting":
                False,

            "contradicting":
                False,

            "word_score":
                word_score,

            "entity_score":
                entity_score,

            "event_score":
                event_score,

            "year_match":
                year_match,
        }

    # ========================================================
    # IRRELEVANT
    # ========================================================

    return {

        "relationship":
            "IRRELEVANT",

        "supporting":
            False,

        "contradicting":
            False,

        "word_score":
            word_score,

        "entity_score":
            entity_score,

        "event_score":
            event_score,

        "year_match":
            year_match,
    }


# ============================================================
# EVIDENCE QUALITY
# ============================================================

def evidence_quality(
    relevance,
    source_trust,
    article_content
):

    quality = (
        relevance * 0.45
        + source_trust * 0.45
        + article_content * 0.10
    )

    return max(
        0.0,
        min(
            1.0,
            quality
        )
    )

# ============================================================
# ML PREDICTION
# ============================================================

def ml_prediction(
    headline,
    article
):

    if not os.path.exists(
        MODEL_PATH
    ):

        raise FileNotFoundError(
            f"V2 model not found: "
            f"{MODEL_PATH}"
        )

    if not os.path.exists(
        VECTORIZER_PATH
    ):

        raise FileNotFoundError(
            f"V2 vectorizer not found: "
            f"{VECTORIZER_PATH}"
        )

    model = joblib.load(
        MODEL_PATH
    )

    vectorizer = joblib.load(
        VECTORIZER_PATH
    )

    text = (
        headline
        + " "
        + article
    )

    X = vectorizer.transform(
        [text]
    )

    prediction = model.predict(
        X
    )[0]

    confidence = None

    if hasattr(
        model,
        "predict_proba"
    ):

        probabilities = (
            model.predict_proba(
                X
            )[0]
        )

        confidence = float(
            max(probabilities)
        )

    elif hasattr(
        model,
        "decision_function"
    ):

        decision = (
            model.decision_function(
                X
            )
        )

        value = float(
            decision[0]
        )

        confidence = (
            1
            /
            (
                1
                +
                math.exp(
                    -abs(value)
                )
            )
        )

    else:

        confidence = 0.50

    label = str(
        prediction
    ).upper()

    if label in {
        "1",
        "TRUE",
        "REAL"
    }:

        label = "REAL"

    else:

        label = "FAKE"

    return (
        label,
        confidence
    )


# ============================================================
# SEARCH QUERY GENERATION
# ============================================================

def build_queries(
    headline,
    article
):

    claim = (
        headline
        + " "
        + article
    )

    entities = list(
        extract_entities(
            claim
        )
    )

    events = list(
        extract_event_groups(
            claim
        )
    )

    queries = []

    # Exact headline
    queries.append(
        headline
    )

    # Headline + entities
    if entities:

        queries.append(
            headline
            + " "
            + " ".join(
                entities[:3]
            )
        )

    # Entity + event
    if entities and events:

        queries.append(
            " ".join(
                entities[:3]
            )
            + " "
            + " ".join(
                events[:2]
            )
        )

    # Fact check
    queries.append(
        headline
        + " fact check"
    )

    # Article-specific
    article_words = [
        word
        for word in tokens(
            article
        )
        if len(word) > 4
    ]

    if article_words:

        queries.append(
            headline
            + " "
            + " ".join(
                article_words[:5]
            )
        )

    return list(
        dict.fromkeys(
            queries
        )
    )


# ============================================================
# EVIDENCE COLLECTION
# ============================================================

def collect_evidence(
    headline,
    article
):

    claim = (
        headline
        + " "
        + article
    )

    claim_type = detect_claim_type(
        claim
    )

    queries = build_queries(
        headline,
        article
    )

    raw_results = []

    for query in queries:

        results = google_news_search(
            query,
            SEARCH_LIMIT
        )

        raw_results.extend(
            results
        )

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique = {}

    for item in raw_results:

        title = (
            item.get(
                "title",
                ""
            )
            .strip()
            .lower()
        )

        if (
            title
            and title not in unique
        ):

            unique[title] = item

    evidence = []

    claim_words = important_tokens(
        claim
    )

    # ========================================================
    # PROCESS RESULTS
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

        rss_combined = (
            title
            + " "
            + summary
        )

        rss_words = important_tokens(
            rss_combined
        )

        relevance = overlap_score(
            claim_words,
            rss_words
        )

        # Ignore extremely weak results
        if relevance < 0.06:

            continue

        # ----------------------------------------------------
        # Publisher
        # ----------------------------------------------------

        domain = get_publisher_domain(
            item
        )

        source_trust = trusted_score(
            domain
        )

        # ----------------------------------------------------
        # V2.1 ARTICLE RETRIEVAL
        # ----------------------------------------------------

        print(
            f"   Retrieving: "
            f"{domain or item.get('source', 'Unknown')}"
        )

        article_content = (
            retrieve_publisher_article(
                item,
                domain
            )
        )

        # ----------------------------------------------------
        # Choose evidence text
        # ----------------------------------------------------

        if article_content:

            content_text = article_content

            evidence_type = (
                "ARTICLE_CONTENT"
            )

            content_bonus = 1.0

        else:

            content_text = summary

            evidence_type = (
                "RSS_SUMMARY"
            )

            content_bonus = 0.0

        # ----------------------------------------------------
        # Relationship
        # ----------------------------------------------------

        relationship = (
            detect_relationship(
                claim,
                title
                + " "
                + content_text,
                claim_type
            )
        )

        # ----------------------------------------------------
        # Quality
        # ----------------------------------------------------

        quality = evidence_quality(
            relevance,
            source_trust,
            content_bonus
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
                item.get(
                    "link",
                    ""
                ),

            "type":
                evidence_type,

            "relevance":
                relevance,

            "claim_overlap":
                relationship[
                    "word_score"
                ],

            "entity_overlap":
                relationship[
                    "entity_score"
                ],

            "event_overlap":
                relationship[
                    "event_score"
                ],

            "year_match":
                relationship[
                    "year_match"
                ],

            "quality":
                quality,

            "trusted":
                source_trust > 0,

            "trust_score":
                source_trust,

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

            "entities":
                list(
                    extract_entities(
                        title
                        + " "
                        + content_text
                    )
                ),

            "events":
                list(
                    extract_event_groups(
                        title
                        + " "
                        + content_text
                    )
                ),
        })

    # ========================================================
    # SORT
    # ========================================================

    evidence.sort(

        key=lambda x: (

            int(
                x["supporting"]
                or x["contradicting"]
            ),

            int(
                x["type"]
                == "ARTICLE_CONTENT"
            ),

            x["trust_score"],

            x["quality"],

            x["relevance"],
        ),

        reverse=True
    )

    return evidence[
        :FINAL_EVIDENCE_LIMIT
    ]


# ============================================================
# FINAL EVIDENCE DECISION
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
        if e["quality"] >= 0.45
    ]

    strong_contradicting = [
        e
        for e in contradicting
        if e["quality"] >= 0.40
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

    support_strength = sum(

        e["quality"]

        * max(

            e["claim_overlap"],

            e["entity_overlap"]
            *
            max(
                e["event_overlap"],
                0.50
            )
        )

        for e in supporting
    )

    contradiction_strength = sum(

        e["quality"]

        * max(

            e["claim_overlap"],

            e["entity_overlap"]
            *
            max(
                e["event_overlap"],
                0.50
            )
        )

        for e in contradicting
    )

    support_strength = min(
        1.0,
        support_strength
    )

    contradiction_strength = min(
        1.0,
        contradiction_strength
    )

    # ========================================================
    # TRUSTED CONTRADICTION
    # ========================================================

    if (
        trusted_contradicting
        and contradiction_strength >= 0.25
    ):

        assessment = "CONTRADICTED"

        score = (

            contradiction_strength
            * 0.60

            + min(
                1.0,
                len(
                    strong_contradicting
                ) / 2
            )
            * 0.25

            + 0.15
        )

        score = min(
            1.0,
            score
        )

    # ========================================================
    # STRONG CONTRADICTION
    # ========================================================

    elif (
        len(
            strong_contradicting
        ) >= 1

        and contradiction_strength >= 0.35
    ):

        assessment = "CONTRADICTED"

        score = (

            contradiction_strength
            * 0.65

            + 0.35
        )

        score = min(
            1.0,
            score
        )

    # ========================================================
    # TRUSTED SUPPORT
    # ========================================================

    elif (
        trusted_supporting
        and support_strength >= 0.25
    ):

        assessment = "SUPPORTED"

        score = (

            support_strength
            * 0.60

            + 0.25

            + min(
                0.15,
                len(
                    trusted_supporting
                ) * 0.05
            )
        )

        score = min(
            1.0,
            score
        )

    # ========================================================
    # MULTIPLE STRONG SUPPORT
    # ========================================================

    elif (
        len(
            strong_supporting
        ) >= 2

        and support_strength >= 0.40
    ):

        assessment = "SUPPORTED"

        score = (

            support_strength
            * 0.65

            + min(
                0.35,
                len(
                    strong_supporting
                ) * 0.12
            )
        )

        score = min(
            1.0,
            score
        )

    # ========================================================
    # SINGLE STRONG SUPPORT
    # ========================================================

    elif (
        len(
            strong_supporting
        ) >= 1

        and support_strength >= 0.50
    ):

        assessment = "SUPPORTED"

        score = min(
            1.0,
            support_strength
            * 0.75
        )

    # ========================================================
    # INCONCLUSIVE
    # ========================================================

    else:

        assessment = "INCONCLUSIVE"

        score = (
            max(
                support_strength,
                contradiction_strength
            )
            * 0.70
        )

    # ========================================================
    # LEVEL
    # ========================================================

    if score >= 0.70:

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

    evidence_assessment = (
        evidence_result[
            "assessment"
        ]
    )

    evidence_score = (
        evidence_result[
            "score"
        ]
    )

    # ========================================================
    # CONTRADICTION
    # ========================================================

    if (
        evidence_assessment
        == "CONTRADICTED"
    ):

        final = "FAKE"

        final_confidence = (

            evidence_score
            * 0.75

            + ml_confidence
            * 0.25
        )

        return (
            final,
            min(
                0.99,
                final_confidence
            )
        )

    # ========================================================
    # SUPPORT
    # ========================================================

    if (
        evidence_assessment
        == "SUPPORTED"
    ):

        final = "REAL"

        final_confidence = (

            evidence_score
            * 0.75

            + ml_confidence
            * 0.25
        )

        return (
            final,
            min(
                0.99,
                final_confidence
            )
        )

    # ========================================================
    # INCONCLUSIVE
    # ========================================================

    final = "NEEDS VERIFICATION"

    final_confidence = (

        evidence_score
        * 0.45

        + ml_confidence
        * 0.55
    )

    return (
        final,
        min(
            0.89,
            final_confidence
        )
    )


# ============================================================
# DISPLAY EVIDENCE
# ============================================================

def print_evidence(
    evidence
):

    print("\n")
    print("-" * 60)
    print("EVIDENCE")
    print("-" * 60)

    if not evidence:

        print(
            "\nNo useful external evidence found."
        )

        return

    for i, e in enumerate(
        evidence,
        1
    ):

        print(
            f"\n[{i}] SOURCE: "
            f"{e['source']}"
        )

        print(
            f"TYPE: "
            f"{e['type']}"
        )

        print(
            f"PUBLISHER: "
            f"{e['publisher']}"
        )

        print(
            f"RELEVANCE: "
            f"{e['relevance'] * 100:.2f}%"
        )

        print(
            f"CLAIM OVERLAP: "
            f"{e['claim_overlap'] * 100:.2f}%"
        )

        print(
            f"ENTITY OVERLAP: "
            f"{e['entity_overlap'] * 100:.2f}%"
        )

        print(
            f"EVENT OVERLAP: "
            f"{e['event_overlap'] * 100:.2f}%"
        )

        print(
            f"YEAR MATCH: "
            f"{e['year_match'] * 100:.2f}%"
        )

        print(
            f"QUALITY: "
            f"{e['quality'] * 100:.2f}%"
        )

        print(
            f"TRUST SCORE: "
            f"{e['trust_score'] * 100:.2f}%"
        )

        print(
            f"TRUSTED SOURCE: "
            f"{'YES' if e['trusted'] else 'NO'}"
        )

        print(
            f"RELATIONSHIP: "
            f"{e['relationship']}"
        )

        print(
            f"SUPPORTING: "
            f"{e['supporting']}"
        )

        print(
            f"CONTRADICTING: "
            f"{e['contradicting']}"
        )

        print(
            f"ENTITIES: "
            f"{e['entities']}"
        )

        print(
            f"EVENT GROUPS: "
            f"{e['events']}"
        )

        print(
            f"TITLE: "
            f"{e['title']}"
        )

        print(
            f"LINK: "
            f"{e['link']}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("V2.1 FULL NEWS ANALYSIS")
    print("=" * 60)

    headline = input(
        "Enter news headline: "
    ).strip()

    article = input(
        "Enter news article: "
    ).strip()

    if not headline:

        print(
            "\nHeadline cannot be empty."
        )

        return

    print(
        "\nAnalyzing news..."
    )

    print(
        "Please wait...\n"
    )

    # ========================================================
    # 1. ML
    # ========================================================

    print(
        "[1/5] Running V2 ML prediction..."
    )

    try:

        ml_label, ml_confidence = (
            ml_prediction(
                headline,
                article
            )
        )

        print(
            f"V2 ML prediction completed: "
            f"{ml_label}"
        )

    except Exception as e:

        print(
            f"\nML ERROR: {e}"
        )

        return

    # ========================================================
    # 2. SEARCH
    # ========================================================

    print(
        "[2/5] Searching external evidence..."
    )

    evidence = collect_evidence(
        headline,
        article
    )

    # ========================================================
    # 3. SCORE
    # ========================================================

    print(
        "[3/5] Scoring evidence relevance..."
    )

    # Already calculated.

    # ========================================================
    # 4. COMPARE
    # ========================================================

    print(
        "[4/5] Comparing evidence with claim..."
    )

    # Already calculated.

    # ========================================================
    # 5. FINAL EVIDENCE
    # ========================================================

    print(
        "[5/5] Calculating evidence confidence..."
    )

    evidence_result = (
        calculate_final_evidence(
            evidence
        )
    )

    (
        final_assessment,
        final_confidence
    ) = calculate_final_decision(

        ml_label,

        ml_confidence,

        evidence_result
    )

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print("\n")

    print("=" * 60)

    print(
        "V2.1 FINAL NEWS ASSESSMENT"
    )

    print("=" * 60)

    print(
        f"ML Prediction: "
        f"{ml_label}"
    )

    print(
        f"ML Confidence: "
        f"{ml_confidence * 100:.2f}%"
    )

    print(
        f"Evidence Assessment: "
        f"{evidence_result['assessment']}"
    )

    print(
        f"Evidence Score: "
        f"{evidence_result['score'] * 100:.2f}%"
    )

    print(
        f"Evidence Level: "
        f"{evidence_result['level']}"
    )

    print(
        f"Final Assessment: "
        f"{final_assessment}"
    )

    print(
        f"Final Confidence: "
        f"{final_confidence * 100:.2f}%"
    )

    print("=" * 60)

    # ========================================================
    # STATISTICS
    # ========================================================

    article_content = sum(

        e["type"]
        == "ARTICLE_CONTENT"

        for e in evidence
    )

    rss_summary = sum(

        e["type"]
        == "RSS_SUMMARY"

        for e in evidence
    )

    trusted_sources = sum(

        e["trusted"]

        for e in evidence
    )

    statistics = {

        "total_evidence":
            len(evidence),

        "article_content":
            article_content,

        "rss_summary":
            rss_summary,

        "trusted_sources":
            trusted_sources,

        "strong_supporting":
            evidence_result[
                "strong_supporting"
            ],

        "strong_contradicting":
            evidence_result[
                "strong_contradicting"
            ],

        "trusted_supporting":
            evidence_result[
                "trusted_supporting"
            ],

        "trusted_contradicting":
            evidence_result[
                "trusted_contradicting"
            ],
    }

    print(
        "\nStatistics:"
    )

    print(
        statistics
    )

    print(
        f"\nStrong Supporting: "
        f"{evidence_result['strong_supporting']}"
    )

    print(
        f"Strong Contradicting: "
        f"{evidence_result['strong_contradicting']}"
    )

    print(
        f"Trusted Supporting: "
        f"{evidence_result['trusted_supporting']}"
    )

    print(
        f"Trusted Contradicting: "
        f"{evidence_result['trusted_contradicting']}"
    )

    print_evidence(
        evidence
    )

    print("\n")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()