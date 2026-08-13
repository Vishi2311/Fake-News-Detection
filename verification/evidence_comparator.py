def compare_evidence(claim, evidence_results, evidence_score=0):
    """
    Compare a claim with retrieved evidence.

    Version 1:
    - SUPPORTED: relevant supporting evidence exists
    - CONTRADICTED: relevant contradictory evidence exists
    - INCONCLUSIVE: evidence is insufficient

    This is an evidence-based assessment, not an absolute
    determination of factual truth.
    """

    claim_words = set(claim.lower().split())

    supporting = []
    contradicting = []

    contradiction_words = {
        "denies",
        "denied",
        "false",
        "incorrect",
        "debunked",
        "rejects",
        "rejected",
        "not true",
        "hoax",
        "misleading"
    }

    for evidence in evidence_results:

        title = evidence.get("title", "")
        title_lower = title.lower()

        relevance_score = evidence.get(
            "relevance_score", 0
        )

        credibility = evidence.get(
            "credibility", "Unknown"
        )

        # Count meaningful matching words
        matching_words = sum(
            1
            for word in claim_words
            if len(word) > 3 and word in title_lower
        )

        # Check for contradiction
        has_contradiction = any(
            phrase in title_lower
            for phrase in contradiction_words
        )

        # -----------------------------
        # CONTRADICTORY EVIDENCE
        # -----------------------------

        if has_contradiction and relevance_score >= 0.4:

            contradicting.append(evidence)

        # -----------------------------
        # SUPPORTING EVIDENCE
        # -----------------------------

        elif (
            matching_words >= 2
            and relevance_score >= 0.4
        ):

            supporting.append(evidence)

    # -----------------------------
    # STRONG EVIDENCE
    # -----------------------------

    # V1 threshold lowered from 0.6 to 0.5
    strong_supporting = [
        item
        for item in supporting
        if item.get("relevance_score", 0) >= 0.5
    ]

    strong_contradicting = [
        item
        for item in contradicting
        if item.get("relevance_score", 0) >= 0.5
    ]

    # -----------------------------
    # TRUSTED EVIDENCE
    # -----------------------------

    trusted_supporting = [
        item
        for item in strong_supporting
        if item.get("credibility") == "Trusted"
    ]

    trusted_contradicting = [
        item
        for item in strong_contradicting
        if item.get("credibility") == "Trusted"
    ]

    # -----------------------------
    # FINAL V1 DECISION
    # -----------------------------

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

    return {
        "assessment": assessment,
        "supporting": supporting,
        "contradicting": contradicting,
        "strong_supporting": strong_supporting,
        "strong_contradicting": strong_contradicting,
        "evidence_score": evidence_score
    }