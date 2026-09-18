# verification/source_checker.py


TRUSTED_SOURCES = {
    # International
    "reuters": "Trusted",
    "reuters.com": "Trusted",
    "associated press": "Trusted",
    "ap news": "Trusted",
    "bbc": "Trusted",
    "bbc news": "Trusted",
    "bbc.com": "Trusted",
    "npr": "Trusted",
    "pbs": "Trusted",
    "cnn": "Trusted",
    "the guardian": "Trusted",

    # Government / official
    "nasa": "Trusted",
    "nasa.gov": "Trusted",
    "who": "Trusted",
    "who.int": "Trusted",
    "un.org": "Trusted",
    "white house": "Trusted",
    "gov.uk": "Trusted",

    # India
    "the hindu": "Trusted",
    "hindustan times": "Trusted",
    "times of india": "Trusted",
    "the times of india": "Trusted",
    "india today": "Trusted",
    "indian express": "Trusted",
    "the indian express": "Trusted",
    "ndtv": "Trusted",
    "moneycontrol": "Trusted",

    # Philippines / fact-checking
    "rappler": "Trusted",
    "inquirer": "Trusted",
    "inquirer.net": "Trusted",

    # Major international publications
    "associated press": "Trusted",
    "time": "Trusted",
    "time magazine": "Trusted",
}


def check_source(source):
    """
    Determine source credibility.

    Returns:
        {
            "source": source_name,
            "credibility": "Trusted" / "Unknown"
        }
    """

    if not source:
        return {
            "source": "",
            "credibility": "Unknown"
        }

    source_clean = source.lower().strip()

    # Direct match
    if source_clean in TRUSTED_SOURCES:
        credibility = TRUSTED_SOURCES[source_clean]

    else:
        credibility = "Unknown"

        # Partial match
        for trusted_source in TRUSTED_SOURCES:

            if (
                trusted_source in source_clean
                or source_clean in trusted_source
            ):
                credibility = TRUSTED_SOURCES[
                    trusted_source
                ]

                break

    return {
        "source": source,
        "credibility": credibility
    }