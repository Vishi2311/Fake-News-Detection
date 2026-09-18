from verification.claim_processor import prepare_claim
from verification.v2_evidence_retriever import search_news_v2
from verification.v2_relevance_scorer import calculate_relevance_v2
from verification.source_checker import check_source
from verification.v2_evidence_scorer import calculate_evidence_score_v2
from verification.v2_evidence_comparator import compare_evidence_v2


def verify_news_v2(title, article, max_results=5):
    """
    Version 2 evidence verification pipeline.

    V1 remains untouched.

    V2 improvements:
    - Attempts article-content retrieval
    - Uses RSS summaries when article content is unavailable
    - Uses evidence type in scoring
    - Uses V2 relevance scoring
    - Tracks evidence statistics
    """

    # --------------------------------
    # 1. PREPARE CLAIM
    # --------------------------------

    claim_data = prepare_claim(
        title,
        article
    )

    # --------------------------------
    # 2. RETRIEVE EVIDENCE
    # --------------------------------

    evidence = search_news_v2(
        claim_data["search_query"],
        max_results=max_results
    )

    # --------------------------------
    # 3. PROCESS EVIDENCE
    # --------------------------------

    for item in evidence:

        source_info = check_source(
            item.get("source", "")
        )

        item["credibility"] = (
            source_info["credibility"]
        )

        article_text = item.get(
            "article_text",
            ""
        )

        item["relevance_score"] = (
            calculate_relevance_v2(
                claim_data["combined_text"],
                item.get("title", ""),
                article_text
            )
        )

    # --------------------------------
    # 4. EVIDENCE SCORE
    # --------------------------------

    evidence_score = calculate_evidence_score_v2(
        evidence
    )

    # --------------------------------
    # 5. COMPARE EVIDENCE
    # --------------------------------

    comparison = compare_evidence_v2(
        claim_data["combined_text"],
        evidence,
        evidence_score["score"]
    )

    assessment = comparison.get(
        "assessment",
        "INCONCLUSIVE"
    )

    # --------------------------------
    # 6. EVIDENCE STATISTICS
    # --------------------------------

    article_content_count = sum(
        1
        for item in evidence
        if item.get("evidence_type")
        == "ARTICLE_CONTENT"
    )

    rss_summary_count = sum(
        1
        for item in evidence
        if item.get("evidence_type")
        == "RSS_SUMMARY"
    )

    title_only_count = sum(
        1
        for item in evidence
        if item.get("evidence_type")
        == "TITLE_ONLY"
    )

    trusted_count = sum(
        1
        for item in evidence
        if item.get("credibility")
        == "Trusted"
    )

    # --------------------------------
    # 7. RETURN V2 RESULT
    # --------------------------------

    return {
        "claim": claim_data,

        "evidence": evidence,

        "assessment": assessment,

        "evidence_score": evidence_score,

        "supporting": comparison[
            "supporting"
        ],

        "contradicting": comparison[
            "contradicting"
        ],

        "strong_supporting": comparison[
            "strong_supporting"
        ],

        "strong_contradicting": comparison[
            "strong_contradicting"
        ],

        "statistics": {
            "total_evidence": len(evidence),

            "article_content": (
                article_content_count
            ),

            "rss_summary": (
                rss_summary_count
            ),

            "title_only": (
                title_only_count
            ),

            "trusted_sources": (
                trusted_count
            )
        }
    }