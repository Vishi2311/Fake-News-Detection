from verification.claim_processor import prepare_claim
from verification.evidence_retriever import search_news
from verification.evidence_comparator import compare_evidence
from verification.source_checker import check_source
from verification.relevance_scorer import calculate_relevance
from verification.evidence_scorer import calculate_evidence_score
def verify_news(title, article, max_results=5):
    """
    Complete Version 1 news verification pipeline.
    """

    # -----------------------------
    # 1. PREPARE CLAIM
    # -----------------------------

    claim_data = prepare_claim(title, article)

    # -----------------------------
    # 2. RETRIEVE EXTERNAL EVIDENCE
    # -----------------------------

    evidence = search_news(
        claim_data["search_query"],
        max_results=max_results
    )

    # -----------------------------
    # 3. PROCESS EVIDENCE
    # -----------------------------

    for item in evidence:

        # Source credibility
        source_info = check_source(
            item.get("source", "")
        )

        item["credibility"] = source_info["credibility"]

        # Relevance
        item["relevance_score"] = calculate_relevance(
            claim_data["combined_text"],
            item.get("title", "")
        )

    # -----------------------------
    # 4. CALCULATE EVIDENCE SCORE
    # -----------------------------

    evidence_score = calculate_evidence_score(
        evidence
    )

    # -----------------------------
    # 5. COMPARE EVIDENCE
    # -----------------------------

    comparison = compare_evidence(
        claim_data["combined_text"],
        evidence,
        evidence_score["score"]
    )

    comparison_result = comparison.get(
        "assessment",
        "INCONCLUSIVE"
    )

    # -----------------------------
    # 6. FINAL V1 ASSESSMENT
    # -----------------------------

    if comparison_result == "SUPPORTED":
        assessment = "SUPPORTED"

    elif comparison_result == "CONTRADICTED":
        assessment = "CONTRADICTED"

    else:
        assessment = "INCONCLUSIVE"

    # -----------------------------
    # 7. RETURN RESULT
    # -----------------------------

    return {
        "claim": claim_data,
        "evidence": evidence,
        "assessment": assessment,
        "evidence_score": evidence_score,
        "supporting": comparison["supporting"],
        "contradicting": comparison["contradicting"],
        "strong_supporting": comparison["strong_supporting"],
        "strong_contradicting": comparison["strong_contradicting"]
    }