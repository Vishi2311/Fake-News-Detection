import re


def clean_text(text):
    """Clean basic unwanted characters from text."""

    if not text:
        return ""

    text = text.strip()
    text = re.sub(r"\s+", " ", text)

    return text


def prepare_claim(title, article):
    """Prepare news text for evidence verification."""

    title = clean_text(title)
    article = clean_text(article)

    combined_text = f"{title}. {article}"

    return {
        "title": title,
        "article": article,
        "combined_text": combined_text,
        "search_query": title
    }