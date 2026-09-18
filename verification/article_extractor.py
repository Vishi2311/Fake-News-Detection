import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def extract_article_text(url, max_chars=10000):
    """
    Attempt to extract readable article text from a webpage.

    Returns:
        {
            "text": extracted text,
            "success": True/False
        }
    """

    if not url:
        return {
            "text": "",
            "success": False
        }

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        if response.status_code != 200:
            return {
                "text": "",
                "success": False
            }

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Remove elements that usually contain
        # navigation, scripts, advertisements, etc.
        for element in soup([
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
            "form"
        ]):
            element.decompose()

        paragraphs = soup.find_all("p")

        text_parts = []

        for paragraph in paragraphs:

            text = paragraph.get_text(
                " ",
                strip=True
            )

            if len(text) >= 40:
                text_parts.append(text)

        article_text = " ".join(
            text_parts
        )

        article_text = " ".join(
            article_text.split()
        )

        if not article_text:
            return {
                "text": "",
                "success": False
            }

        return {
            "text": article_text[:max_chars],
            "success": True
        }

    except Exception:
        return {
            "text": "",
            "success": False
        }