def calculate_evidence_score_v2(
    evidence_results,
    comparison_result=None
):
    """
    V2.5 Evidence Scorer

    Scores the strength of external evidence.

    Priority:
    1. Trusted fact-check / contradiction
    2. Multiple strong contradictions
    3. Trusted supporting evidence
    4. Multiple strong supporting sources
    5. General relevance

    Important:
    Evidence score measures the strength of the available evidence.
    It is NOT the probability that the news is fake.
    """

    if not evidence_results:
        return {
            "score": 0.0,
            "level": "WEAK"
        }

    # ============================================================
    # IF COMPARATOR RESULT IS AVAILABLE
    # ============================================================

    if comparison_result is None:
        comparison_result = {}

    supporting = comparison_result.get(
        "supporting",
        []
    )

    contradicting = comparison_result.get(
        "contradicting",
        []
    )

    strong_supporting = comparison_result.get(
        "strong_supporting",
        []
    )

    strong_contradicting = comparison_result.get(
        "strong_contradicting",
        []
    )

    trusted_supporting = comparison_result.get(
        "trusted_supporting",
        []
    )

    trusted_contradicting = comparison_result.get(
        "trusted_contradicting",
        []
    )

    # ============================================================
    # FACT CHECK DETECTION
    # ============================================================

    fact_check_terms = [
        "fact check",
        "fact-check",
        "factcheck",
        "debunked",
        "debunk",
        "fake claim",
        "false claim",
        "hoax",
        "misleading",
        "false information",
        "false report"
    ]

    # ============================================================
    # HELPER
    # ============================================================

    def is_fact_check(item):

        title = str(
            item.get(
                "title",
                ""
            )
        ).lower()

        return any(
            term in title
            for term in fact_check_terms
        )

    def relevance(item):

        try:
            return float(
                item.get(
                    "relevance_score",
                    0
                )
            )

        except (
            ValueError,
            TypeError
        ):

            return 0.0

    def is_trusted(item):

        return (
            str(
                item.get(
                    "credibility",
                    "Unknown"
                )
            ).lower()
            == "trusted"
        )

    # ============================================================
    # BASE EVIDENCE SCORE
    # ============================================================

    weighted_scores = []
    total_weight = 0.0

    for item in evidence_results:

        rel = relevance(item)

        if rel < 0.05:
            continue

        # --------------------------------------------------------
        # SOURCE WEIGHT
        # --------------------------------------------------------

        if is_trusted(item):
            source_weight = 1.5
        else:
            source_weight = 0.7

        # --------------------------------------------------------
        # EVIDENCE TYPE
        # --------------------------------------------------------

        evidence_type = item.get(
            "evidence_type",
            "TITLE_ONLY"
        )

        if evidence_type == "ARTICLE_CONTENT":

            type_weight = 1.5

        elif evidence_type == "RSS_SUMMARY":

            type_weight = 1.0

        else:

            type_weight = 0.7

        # --------------------------------------------------------
        # RELEVANCE
        # --------------------------------------------------------

        if rel >= 0.70:

            relevance_weight = 1.5

        elif rel >= 0.50:

            relevance_weight = 1.25

        elif rel >= 0.30:

            relevance_weight = 0.90

        elif rel >= 0.15:

            relevance_weight = 0.50

        else:

            relevance_weight = 0.20

        # --------------------------------------------------------
        # FACT CHECK BONUS
        # --------------------------------------------------------

        if is_fact_check(item):

            fact_check_weight = 2.0

        else:

            fact_check_weight = 1.0

        # --------------------------------------------------------
        # FINAL WEIGHT
        # --------------------------------------------------------

        weight = (
            source_weight
            * type_weight
            * relevance_weight
            * fact_check_weight
        )

        contribution = rel * 100

        weighted_scores.append(
            contribution * weight
        )

        total_weight += weight

    # ============================================================
    # BASE SCORE
    # ============================================================

    if total_weight == 0:

        score = 0.0

    else:

        score = (
            sum(weighted_scores)
            / total_weight
        )

    # ============================================================
    # STRONG TRUSTED FACT-CHECK CONTRADICTION
    # ============================================================

    trusted_fact_checks = [

        item

        for item in trusted_contradicting

        if is_fact_check(item)
    ]

    # ============================================================
    # TWO OR MORE TRUSTED FACT CHECKS
    # ============================================================

    if len(trusted_fact_checks) >= 2:

        score = max(
            score,
            85.0
        )

    # ============================================================
    # ONE TRUSTED FACT CHECK
    # ============================================================

    elif len(trusted_fact_checks) == 1:

        rel = relevance(
            trusted_fact_checks[0]
        )

        if rel >= 0.50:

            score = max(
                score,
                80.0
            )

        else:

            score = max(
                score,
                70.0
            )

    # ============================================================
    # MULTIPLE TRUSTED CONTRADICTIONS
    # ============================================================

    if len(trusted_contradicting) >= 2:

        score = max(
            score,
            80.0
        )

    # ============================================================
    # STRONG CONTRADICTION
    # ============================================================

    if len(strong_contradicting) >= 2:

        score = max(
            score,
            75.0
        )

    elif len(strong_contradicting) == 1:

        score = max(
            score,
            65.0
        )

    # ============================================================
    # TRUSTED SUPPORTING EVIDENCE
    # ============================================================

    if len(trusted_supporting) >= 2:

        score = max(
            score,
            70.0
        )

    elif len(trusted_supporting) == 1:

        score = max(
            score,
            60.0
        )

    # ============================================================
    # STRONG SUPPORTING EVIDENCE
    # ============================================================

    if len(strong_supporting) >= 3:

        score = max(
            score,
            60.0
        )

    elif len(strong_supporting) >= 2:

        score = max(
            score,
            55.0
        )

    # ============================================================
    # CAP SCORE
    # ============================================================

    score = round(
        min(
            max(score, 0.0),
            100.0
        ),
        2
    )

    # ============================================================
    # EVIDENCE LEVEL
    # ============================================================

    if score >= 70:

        level = "STRONG"

    elif score >= 45:

        level = "MODERATE"

    else:

        level = "WEAK"

    # ============================================================
    # RETURN
    # ============================================================

    return {
        "score": score,
        "level": level
    }


# ================================================================
# STANDALONE TEST
# ================================================================

if __name__ == "__main__":

    print(
        "V2 EVIDENCE SCORER TEST"
    )

    print(
        "=" * 50
    )

    sample_evidence = [

        {
            "title":
                "FACT CHECK: News graphic claiming ICC will release Duterte is fake",

            "relevance_score":
                0.27,

            "credibility":
                "Trusted",

            "evidence_type":
                "RSS_SUMMARY"
        },

        {
            "title":
                "FACT CHECK: No ICC ruling ordering Duterte's release",

            "relevance_score":
                0.27,

            "credibility":
                "Trusted",

            "evidence_type":
                "RSS_SUMMARY"
        }
    ]

    comparison = {

        "supporting": [],

        "contradicting":
            sample_evidence,

        "strong_supporting": [],

        "strong_contradicting":
            sample_evidence,

        "trusted_supporting": [],

        "trusted_contradicting":
            sample_evidence
    }

    result = calculate_evidence_score_v2(
        sample_evidence,
        comparison
    )

    print(
        "Evidence Score:",
        result["score"]
    )

    print(
        "Evidence Level:",
        result["level"]
    )