import feedparser
from bs4 import BeautifulSoup
from urllib.parse import quote


# ============================================================
# GOOGLE NEWS RSS
# ============================================================

def extract_rss_summary(summary):
    """
    Clean HTML from Google News RSS summary.
    """

    if not summary:
        return ""

    try:

        soup = BeautifulSoup(
            summary,
            "html.parser"
        )

        text = soup.get_text(
            " ",
            strip=True
        )

        return " ".join(
            text.split()
        )

    except Exception:

        return ""


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):
    """
    Normalize text for duplicate detection
    and search classification.
    """

    if not text:
        return ""

    text = str(text).lower()

    replacements = {
        "’": "'",
        "‘": "'",
        "–": "-",
        "—": "-"
    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )

    return " ".join(
        text.split()
    )


# ============================================================
# SEARCH QUERY BUILDER
# ============================================================

def build_search_queries(query):
    """
    Create multiple evidence-search queries.

    Search categories:

    1. Original claim
    2. Fact check
    3. False
    4. Fake
    5. Debunked
    6. No evidence
    """

    query = str(
        query or ""
    ).strip()

    if not query:
        return []

    return [

        {
            "query": query,
            "type": "ORIGINAL"
        },

        {
            "query": f"{query} fact check",
            "type": "FACT_CHECK"
        },

        {
            "query": f"{query} false",
            "type": "FALSE_CLAIM"
        },

        {
            "query": f"{query} fake",
            "type": "FAKE_CLAIM"
        },

        {
            "query": f"{query} debunked",
            "type": "DEBUNK"
        },

        {
            "query": f"{query} no evidence",
            "type": "NO_EVIDENCE"
        }

    ]


# ============================================================
# FETCH GOOGLE NEWS
# ============================================================

def fetch_google_news(query):
    """
    Fetch Google News RSS results.

    Individual article pages are NOT opened.
    """

    if not query:
        return []

    encoded_query = quote(
        query
    )

    url = (
        "https://news.google.com/rss/search?"
        f"q={encoded_query}"
        "&hl=en-IN"
        "&gl=IN"
        "&ceid=IN:en"
    )

    try:

        feed = feedparser.parse(
            url
        )

        return feed.entries

    except Exception:

        return []


# ============================================================
# PROCESS RSS ENTRY
# ============================================================

def process_entry(
    entry,
    search_type="ORIGINAL"
):
    """
    Convert one Google News RSS entry
    into standard V2 evidence format.
    """

    # --------------------------------------------------------
    # SOURCE
    # --------------------------------------------------------

    source_name = ""

    try:

        if "source" in entry:

            source_name = entry.source.get(
                "title",
                ""
            )

    except Exception:

        source_name = ""

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    title = entry.get(
        "title",
        ""
    )

    link = entry.get(
        "link",
        ""
    )

    published = entry.get(
        "published",
        ""
    )

    # --------------------------------------------------------
    # RSS SUMMARY
    # --------------------------------------------------------

    summary = entry.get(
        "summary",
        ""
    )

    summary_text = extract_rss_summary(
        summary
    )

    # --------------------------------------------------------
    # EVIDENCE TYPE
    # --------------------------------------------------------

    if len(summary_text) >= 50:

        article_text = summary_text[
            :5000
        ]

        evidence_type = (
            "RSS_SUMMARY"
        )

        extraction_status = (
            "RSS_SUMMARY_AVAILABLE"
        )

    else:

        article_text = ""

        evidence_type = (
            "TITLE_ONLY"
        )

        extraction_status = (
            "TITLE_ONLY"
        )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "title":
            title,

        "link":
            link,

        "published":
            published,

        "source":
            source_name,

        "article_text":
            article_text,

        "evidence_type":
            evidence_type,

        "extraction_status":
            extraction_status,

        # Important:
        # remembers which search produced
        # this evidence.
        "search_type":
            search_type
    }


# ============================================================
# EVIDENCE PRIORITY
# ============================================================

def get_search_priority(
    search_type
):
    """
    Assign priority to evidence.

    Fact-check and debunk searches receive
    higher priority because they are particularly
    useful for detecting false claims.
    """

    priorities = {

        "FACT_CHECK":
            100,

        "DEBUNK":
            95,

        "FALSE_CLAIM":
            90,

        "FAKE_CLAIM":
            90,

        "NO_EVIDENCE":
            80,

        "ORIGINAL":
            50
    }

    return priorities.get(
        search_type,
        40
    )


# ============================================================
# FACT-CHECK TITLE DETECTION
# ============================================================

def looks_like_fact_check(
    title
):
    """
    Detect fact-check style headlines.
    """

    title = normalize_text(
        title
    )

    fact_check_terms = {

        "fact check",
        "fact-check",
        "debunked",
        "debunk",
        "fake claim",
        "false claim",
        "false report",
        "false information",
        "hoax",
        "misleading",
        "untrue",
        "not true",
        "no evidence",
        "no ruling"
    }

    for term in fact_check_terms:

        if term in title:

            return True

    return False


# ============================================================
# SUPPORT / CONTRADICTION HINT
# ============================================================

def classify_search_hint(
    result
):
    """
    Give the pipeline a useful hint about
    why the evidence was retrieved.

    This does NOT make the final decision.
    The comparator still decides support/
    contradiction.
    """

    search_type = result.get(
        "search_type",
        "ORIGINAL"
    )

    title = result.get(
        "title",
        ""
    )

    if looks_like_fact_check(
        title
    ):

        return "FACT_CHECK"

    if search_type in {
        "FACT_CHECK",
        "DEBUNK",
        "FALSE_CLAIM",
        "FAKE_CLAIM",
        "NO_EVIDENCE"
    }:

        return "POTENTIAL_CONTRADICTION"

    return "GENERAL_EVIDENCE"


# ============================================================
# SEARCH NEWS V2
# ============================================================

def search_news_v2(
    query,
    max_results=5
):
    """
    V2 evidence retrieval engine.

    Improvements over the previous version:

    - Runs ALL evidence searches.
    - Does not stop after the first search.
    - Removes duplicates after collecting everything.
    - Prioritizes fact-check/debunking results.
    - Keeps RSS-only retrieval for stability.
    """

    if not query:

        return []

    query = str(
        query
    ).strip()

    if not query:

        return []

    try:

        max_results = int(
            max_results
        )

    except (
        TypeError,
        ValueError
    ):

        max_results = 5

    if max_results <= 0:

        max_results = 5

    # --------------------------------------------------------
    # BUILD SEARCH QUERIES
    # --------------------------------------------------------

    search_queries = build_search_queries(
        query
    )

    if not search_queries:

        return []

    all_results = []

    # --------------------------------------------------------
    # RUN ALL SEARCHES
    # --------------------------------------------------------

    for search_item in search_queries:

        search_query = search_item[
            "query"
        ]

        search_type = search_item[
            "type"
        ]

        try:

            entries = fetch_google_news(
                search_query
            )

        except Exception:

            entries = []

        if not entries:

            continue

        for entry in entries:

            try:

                result = process_entry(
                    entry,
                    search_type
                )

                # Add classification hint.
                result[
                    "search_hint"
                ] = classify_search_hint(
                    result
                )

                # Add retrieval priority.
                result[
                    "search_priority"
                ] = get_search_priority(
                    search_type
                )

                all_results.append(
                    result
                )

            except Exception:

                continue

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    unique_results = []

    seen_links = set()

    seen_titles = set()

    for result in all_results:

        link = str(
            result.get(
                "link",
                ""
            )
        ).strip()

        title = str(
            result.get(
                "title",
                ""
            )
        ).strip()

        title_key = normalize_text(
            title
        )

        # ----------------------------------------------------
        # Prefer link as identifier.
        # ----------------------------------------------------

        identifier = (
            link
            if link
            else title_key
        )

        if not identifier:

            continue

        # ----------------------------------------------------
        # Duplicate link
        # ----------------------------------------------------

        if link:

            if link in seen_links:

                continue

        # ----------------------------------------------------
        # Duplicate title
        # ----------------------------------------------------

        if title_key:

            if title_key in seen_titles:

                continue

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        if link:

            seen_links.add(
                link
            )

        if title_key:

            seen_titles.add(
                title_key
            )

        unique_results.append(
            result
        )

    # ========================================================
    # SORT RESULTS
    # ========================================================

    # Fact-check/debunk evidence is prioritized,
    # but original evidence is still retained.
    unique_results.sort(
        key=lambda item: (
            item.get(
                "search_priority",
                0
            ),
            len(
                item.get(
                    "article_text",
                    ""
                )
            )
        ),
        reverse=True
    )

    # ========================================================
    # RETURN TOP RESULTS
    # ========================================================

    return unique_results[
        :max_results
    ]


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 60
    )

    print(
        "V2 EVIDENCE RETRIEVER TEST"
    )

    print(
        "=" * 60
    )

    query = input(
        "Enter search query: "
    ).strip()

    if not query:

        print(
            "Search query cannot be empty."
        )

        raise SystemExit(1)

    print()

    print(
        "Searching Google News RSS..."
    )

    results = search_news_v2(
        query,
        max_results=5
    )

    print()

    print(
        "Results:",
        len(results)
    )

    print()

    for index, item in enumerate(
        results,
        start=1
    ):

        print(
            f"[{index}]",
            item.get(
                "source",
                "Unknown"
            )
        )

        print(
            "TYPE:",
            item.get(
                "evidence_type",
                "UNKNOWN"
            )
        )

        print(
            "SEARCH TYPE:",
            item.get(
                "search_type",
                "UNKNOWN"
            )
        )

        print(
            "SEARCH HINT:",
            item.get(
                "search_hint",
                "UNKNOWN"
            )
        )

        print(
            "PRIORITY:",
            item.get(
                "search_priority",
                0
            )
        )

        print(
            "TITLE:",
            item.get(
                "title",
                ""
            )
        )

        print(
            "SUMMARY LENGTH:",
            len(
                item.get(
                    "article_text",
                    ""
                )
            )
        )

        print()