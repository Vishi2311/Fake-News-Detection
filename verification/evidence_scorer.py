def calculate_evidence_score(evidence):
    """
    Calculate an overall evidence score using:
    - source credibility
    - evidence relevance
    - primary-source weighting
    """

    if not evidence:
        return {
            "score": 0,
            "level": "NO EVIDENCE"
        }

    total_weighted_score = 0
    total_weight = 0

    for item in evidence:

        # -----------------------------
        # 1. SOURCE CREDIBILITY
        # -----------------------------
        credibility = item.get("credibility", "Unknown")

        if credibility == "Trusted":
            source_score = 1.0
        else:
            source_score = 0.5

        # -----------------------------
        # 2. RELEVANCE
        # -----------------------------
        relevance = item.get("relevance_score", 0)

        # Keep relevance between 0 and 1
        relevance = max(0, min(relevance, 1))

        # -----------------------------
        # 3. PRIMARY SOURCE BONUS
        # -----------------------------
        title = item.get("title", "").lower()
        source = item.get("source", "").lower()
        link = item.get("link", "").lower()

        primary_source_bonus = 1.0

        # Official government / organization source
        if (
            ".gov" in source
            or ".gov" in link
            or "nasa" in source
            or "nasa.gov" in link
        ):
            primary_source_bonus = 1.5

        # -----------------------------
        # 4. FINAL ITEM SCORE
        # -----------------------------
        item_score = (
            source_score
            * relevance
            * primary_source_bonus
        )

        # Cap individual contribution
        item_score = min(item_score, 1.0)

        total_weighted_score += item_score
        total_weight += 1

    # -----------------------------
    # 5. OVERALL SCORE
    # -----------------------------
    final_score = total_weighted_score / total_weight

    percentage = round(final_score * 100, 2)

    # -----------------------------
    # 6. EVIDENCE LEVEL
    # -----------------------------
    if percentage >= 70:
        level = "STRONG"

    elif percentage >= 45:
        level = "MODERATE"

    elif percentage > 0:
        level = "WEAK"

    else:
        level = "NO EVIDENCE"

    return {
        "score": percentage,
        "level": level
    }