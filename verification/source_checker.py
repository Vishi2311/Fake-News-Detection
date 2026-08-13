TRUSTED_SOURCES = {
    "reuters",
    "associated press",
    "apnews",
    "bbc",
    "bbc news",
    "the guardian",
    "theguardian",
    "ndtv",
    "india today",
    "the economic times",
    "economic times",
    "dd india",
    "doordarshan",
    "the hindu",
    "times of india",
    "hindustan times",
    "indian express",
    "business standard",
    "business-standard.com",
    "news on air",
    "nasa",
    "nasa.gov",
    "who",
    "who.int",
    "un",
    "un.org",
    "gov.in"
}


def check_source(source_name):
    """
    Check whether the publisher is present
    in the predefined trusted-source list.
    """

    if not source_name:
        return {
            "source": "",
            "credibility": "Unknown"
        }

    source = source_name.lower().strip()

    for trusted_source in TRUSTED_SOURCES:
        if trusted_source in source:
            return {
                "source": source_name,
                "credibility": "Trusted"
            }

    return {
        "source": source_name,
        "credibility": "Unknown"
    }