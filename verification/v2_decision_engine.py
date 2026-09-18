
"""
V2 Decision Engine
------------------

Combines:
1. ML prediction
2. ML confidence
3. External evidence assessment
4. Strong/trusted supporting evidence
5. Strong/trusted contradicting evidence

Priority:
- Strong trusted contradiction -> FAKE
- Strong trusted support -> REAL
- Strong contradiction -> FAKE
- Strong support -> REAL
- Otherwise -> NEEDS VERIFICATION
"""


def make_final_decision(
    ml_prediction,
    ml_confidence,
    evidence_assessment,
    evidence_score,
    evidence_level,
    strong_supporting_count=0,
    strong_contradicting_count=0,
    trusted_supporting_count=0,
    trusted_contradicting_count=0,
):
    """
    Make the final V2 news assessment.

    Returns:
        {
            "final_assessment": "REAL" / "FAKE" / "NEEDS VERIFICATION",
            "reason": "...",
            "final_confidence": float
        }
    """

    ml_prediction = str(
        ml_prediction
    ).upper().strip()

    evidence_assessment = str(
        evidence_assessment
    ).upper().strip()

    evidence_level = str(
        evidence_level
    ).upper().strip()

    ml_confidence = float(
        ml_confidence or 0
    )

    evidence_score = float(
        evidence_score or 0
    )

    strong_supporting_count = int(
        strong_supporting_count or 0
    )

    strong_contradicting_count = int(
        strong_contradicting_count or 0
    )

    trusted_supporting_count = int(
        trusted_supporting_count or 0
    )

    trusted_contradicting_count = int(
        trusted_contradicting_count or 0
    )

    # ==========================================================
    # 1. HIGHEST PRIORITY — TRUSTED CONTRADICTING EVIDENCE
    # ==========================================================

    if trusted_contradicting_count > 0:

        final_confidence = max(
            70.0,
            evidence_score
        )

        return {
            "final_assessment": "FAKE",
            "reason": (
                "Trusted external evidence "
                "contradicts the claim."
            ),
            "final_confidence": round(
                min(final_confidence, 99.0),
                2
            )
        }

    # ==========================================================
    # 2. HIGHEST PRIORITY — TRUSTED SUPPORTING EVIDENCE
    # ==========================================================

    if trusted_supporting_count >= 2:

        final_confidence = max(
            70.0,
            evidence_score
        )

        return {
            "final_assessment": "REAL",
            "reason": (
                "Multiple trusted external sources "
                "strongly support the claim."
            ),
            "final_confidence": round(
                min(final_confidence, 99.0),
                2
            )
        }

    # One trusted supporting source + strong evidence
    if (
        trusted_supporting_count == 1
        and strong_supporting_count >= 2
        and evidence_score >= 50
    ):

        final_confidence = max(
            65.0,
            evidence_score
        )

        return {
            "final_assessment": "REAL",
            "reason": (
                "Trusted external evidence supports "
                "the claim and additional strong "
                "evidence agrees."
            ),
            "final_confidence": round(
                min(final_confidence, 95.0),
                2
            )
        }

    # ==========================================================
    # 3. STRONG CONTRADICTING EVIDENCE
    # ==========================================================

    if (
        strong_contradicting_count >= 2
        and evidence_score >= 60
    ):

        final_confidence = max(
            65.0,
            evidence_score
        )

        return {
            "final_assessment": "FAKE",
            "reason": (
                "Strong external evidence "
                "contradicts the claim."
            ),
            "final_confidence": round(
                min(final_confidence, 95.0),
                2
            )
        }

    # ==========================================================
    # 4. STRONG SUPPORTING EVIDENCE
    # ==========================================================

    if (
        strong_supporting_count >= 2
        and evidence_score >= 55
    ):

        final_confidence = max(
            60.0,
            evidence_score
        )

        return {
            "final_assessment": "REAL",
            "reason": (
                "Strong external evidence "
                "supports the claim."
            ),
            "final_confidence": round(
                min(final_confidence, 95.0),
                2
            )
        }

    # ==========================================================
    # 5. CLEAR ML + EVIDENCE AGREEMENT
    # ==========================================================

    if (
        ml_prediction == "REAL"
        and evidence_assessment == "SUPPORTED"
        and evidence_score >= 45
    ):

        final_confidence = (
            ml_confidence * 0.45
            + evidence_score * 0.55
        )

        return {
            "final_assessment": "REAL",
            "reason": (
                "The ML prediction agrees with "
                "supporting external evidence."
            ),
            "final_confidence": round(
                min(final_confidence, 95.0),
                2
            )
        }

    if (
        ml_prediction == "FAKE"
        and evidence_assessment == "CONTRADICTED"
        and evidence_score >= 45
    ):

        final_confidence = (
            ml_confidence * 0.45
            + evidence_score * 0.55
        )

        return {
            "final_assessment": "FAKE",
            "reason": (
                "The ML prediction agrees with "
                "contradicting external evidence."
            ),
            "final_confidence": round(
                min(final_confidence, 95.0),
                2
            )
        }

    # ==========================================================
    # 6. ML + EVIDENCE DISAGREEMENT
    # ==========================================================

    if (
        ml_prediction == "REAL"
        and evidence_assessment == "CONTRADICTED"
    ):

        return {
            "final_assessment": "NEEDS VERIFICATION",
            "reason": (
                "The ML prediction and external "
                "evidence disagree."
            ),
            "final_confidence": round(
                max(
                    ml_confidence,
                    evidence_score
                ),
                2
            )
        }

    if (
        ml_prediction == "FAKE"
        and evidence_assessment == "SUPPORTED"
    ):

        return {
            "final_assessment": "NEEDS VERIFICATION",
            "reason": (
                "The ML prediction and external "
                "evidence disagree."
            ),
            "final_confidence": round(
                max(
                    ml_confidence,
                    evidence_score
                ),
                2
            )
        }

    # ==========================================================
    # 7. MODERATE EVIDENCE
    # ==========================================================

    if evidence_level == "MODERATE":

        return {
            "final_assessment": "NEEDS VERIFICATION",
            "reason": (
                "Evidence exists, but it is not "
                "strong enough to establish the claim."
            ),
            "final_confidence": round(
                evidence_score,
                2
            )
        }

    # ==========================================================
    # 8. WEAK / INCONCLUSIVE EVIDENCE
    # ==========================================================

    return {
        "final_assessment": "NEEDS VERIFICATION",
        "reason": (
            "Available external evidence is "
            "insufficient to establish the claim."
        ),
        "final_confidence": round(
            evidence_score,
            2
        )
    }
