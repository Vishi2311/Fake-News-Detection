import feedparser
from urllib.parse import quote


def search_news(query, max_results=5):
    """
    Search Google News RSS for articles related to a query.
    """

    encoded_query = quote(query)

    url = (
        "https://news.google.com/rss/search?"
        f"q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    )

    feed = feedparser.parse(url)

    results = []

    for entry in feed.entries[:max_results]:

        source_name = ""

        if "source" in entry:
            source_name = entry.source.get("title", "")

        results.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "source": source_name
        })

    return results