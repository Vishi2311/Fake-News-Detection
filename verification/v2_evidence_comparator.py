import re


def normalize_text(text):
    """Normalize text for reliable comparison."""

    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"[^a-z0-9\s-]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def compare_evidence_v2(
    claim,
    evidence_results,
    evidence_score=0
):
    """
    V2.5 Evidence Comparator

    Classifies evidence as:
        SUPPORTING
        CONTRADICTING
        NEUTRAL

    Important improvements:
    - Explicit fact-check headlines receive priority.
    - "fake", "false", "debunked", etc. are treated as contradiction signals.
    - Fact-check evidence can contradict a claim even when normal
      semantic relevance is below the normal supporting threshold.
    - Trusted fact-check evidence receives the highest priority.
    - Weak/unrelated evidence remains neutral.
    - Ordinary words such as "ordered", "will", "announced" do not
      automatically prove a claim.
    """

    supporting = []
    contradicting = []
    neutral = []

    claim_clean = normalize_text(claim)

    claim_words = set(
        claim_clean.split()
    )

    # ============================================================
    # EXPLICIT CONTRADICTION PHRASES
    # ============================================================

    contradiction_phrases = [
        "fact check",
        "fact-check",
        "factcheck",
        "is fake",
        "is false",
        "fake claim",
        "false claim",
        "fake news",
        "false news",
        "debunked",
        "debunk",
        "denied",
        "denies",
        "rejected",
        "rejects",
        "incorrect",
        "untrue",
        "hoax",
        "misleading",
        "no evidence",
        "did not happen",
        "didnt happen",
        "did not",
        "didnt",
        "never happened",
        "not true",
        "not real",
        "fabricated",
        "false information",
        "false report",
        "claim is false",
        "claim was false",
        "claim is fake",
        "claim was fake",
        "ruling does not exist",
        "no ruling",
        "no order",
        "no such order",
        "no such ruling",
    ]

    # ============================================================
    # SUPPORT PHRASES
    # ============================================================

    support_phrases = [
        "confirmed",
        "confirms",
        "verified",
        "officially announced",
        "official announcement",
        "official statement",
        "according to",
        "reports",
        "reported",
        "announced",
        "approved",
        "approves",
        "plans to",
        "will launch",
        "has launched",
        "launched",
        "has ordered",
    ]

    # ============================================================
    # FACT-CHECK IDENTIFIERS
    # ============================================================

    fact_check_identifiers = [
        "fact check",
        "fact-check",
        "factcheck",
        "debunked",
        "debunk",
        "hoax",
        "false claim",
        "fake claim",
    ]

    # ============================================================
    # PROCESS EVIDENCE
    # ============================================================

    for evidence in evidence_results:

        title = evidence.get(
            "title",
            ""
        )

        article_text = evidence.get(
            "article_text",
            ""
        )

        relevance = float(
            evidence.get(
                "relevance_score",
                0
            )
        )

        credibility = evidence.get(
            "credibility",
            "Unknown"
        )

        evidence_type = evidence.get(
            "evidence_type",
            "TITLE_ONLY"
        )

        title_clean = normalize_text(
            title
        )

        article_clean = normalize_text(
            article_text
        )

        evidence_text = (
            title_clean
            + " "
            + article_clean
        )

        evidence_words = set(
            evidence_text.split()
        )

        # ========================================================
        # CLAIM WORD OVERLAP
        # ========================================================

        matching_words = {
            word
            for word in claim_words
            if len(word) > 3
            and word in evidence_words
        }

        matching_count = len(
            matching_words
        )

        # ========================================================
        # FACT CHECK DETECTION
        # ========================================================

        fact_check_found = any(
            phrase in evidence_text
            for phrase in fact_check_identifiers
        )

        # ========================================================
        # CONTRADICTION DETECTION
        # ========================================================

        contradiction_found = any(
            phrase in evidence_text
            for phrase in contradiction_phrases
        )

        # ========================================================
        # SUPPORT DETECTION
        # ========================================================

        support_found = any(
            phrase in evidence_text
            for phrase in support_phrases
        )

        # ========================================================
        # SPECIAL RULE:
        # EXPLICIT FACT-CHECK CONTRADICTION
        # ========================================================
        #
        # Example:
        #
        # Claim:
        # Trump ordered Duterte release...
        #
        # Evidence:
        # FACT CHECK: News graphic claiming ICC will release
        # Duterte is fake
        #
        # Even if relevance is only 0.27, the evidence is clearly
        # about the same claim and explicitly says it is fake.
        #
        # Therefore it should be contradiction evidence.
        # ========================================================

        if (
            fact_check_found
            and contradiction_found
            and relevance >= 0.25
        ):

            contradicting.append(
                evidence
            )

            continue

        # ========================================================
        # STRONG EXPLICIT CONTRADICTION
        # ========================================================

        if (
            contradiction_found
            and relevance >= 0.45
        ):

            contradicting.append(
                evidence
            )

            continue

        # ========================================================
        # IGNORE VERY WEAK EVIDENCE
        # ========================================================

        if relevance < 0.40:

            neutral.append(
                evidence
            )

            continue

        # ========================================================
        # SUPPORTING EVIDENCE
        # ========================================================

        if (
            support_found
            and matching_count >= 2
            and relevance >= 0.50
        ):

            supporting.append(
                evidence
            )

        elif (
            matching_count >= 3
            and relevance >= 0.60
        ):

            supporting.append(
                evidence
            )

        else:

            neutral.append(
                evidence
            )

    # ============================================================
    # STRONG SUPPORTING
    # ============================================================

    strong_supporting = [

        item
        for item in supporting

        if float(
            item.get(
                "relevance_score",
                0
            )
        ) >= 0.60
    ]

    # ============================================================
    # STRONG CONTRADICTING
    # ============================================================

    strong_contradicting = [

        item
        for item in contradicting

        if (
            float(
                item.get(
                    "relevance_score",
                    0
                )
            ) >= 0.50

            or

            (
                any(
                    phrase in normalize_text(
                        item.get(
                            "title",
                            ""
                        )
                    )
                    for phrase in fact_check_identifiers
                )

                and

                float(
                    item.get(
                        "relevance_score",
                        0
                    )
                ) >= 0.25
            )
        )
    ]

    # ============================================================
    # TRUSTED SUPPORTING
    # ============================================================

    trusted_supporting = [

        item

        for item in strong_supporting

        if str(
            item.get(
                "credibility",
                "Unknown"
            )
        ).lower() == "trusted"
    ]

    # ============================================================
    # TRUSTED CONTRADICTING
    # ============================================================

    trusted_contradicting = [

        item

        for item in strong_contradicting

        if str(
            item.get(
                "credibility",
                "Unknown"
            )
        ).lower() == "trusted"
    ]

    # ============================================================
    # FINAL EVIDENCE ASSESSMENT
    # ============================================================

    if trusted_contradicting:

        assessment = "CONTRADICTED"

    elif trusted_supporting:

        assessment = "SUPPORTED"

    elif strong_contradicting:

        assessment = "CONTRADICTED"

    elif strong_supporting:

        assessment = "SUPPORTED"

    else:

        assessment = "INCONCLUSIVE"

    # ============================================================
    # RETURN
    # ============================================================

    return {

        "assessment":
            assessment,

        "supporting":
            supporting,

        "contradicting":
            contradicting,

        "neutral":
            neutral,

        "strong_supporting":
            strong_supporting,

        "strong_contradicting":
            strong_contradicting,

        "trusted_supporting":
            trusted_supporting,

        "trusted_contradicting":
            trusted_contradicting,

        "evidence_score":
            evidence_score
    }