import streamlit as st
import sys
import os

# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VERIFICATION_DIR = os.path.join(
    BASE_DIR,
    "verification"
)

if VERIFICATION_DIR not in sys.path:
    sys.path.insert(0, VERIFICATION_DIR)


# ============================================================
# IMPORT V2 PIPELINE
# ============================================================

try:
    from v2_full_pipeline import (
        ml_prediction,
        collect_evidence,
        calculate_final_evidence,
        calculate_final_decision
    )

    IMPORT_ERROR = None

except Exception as e:
    IMPORT_ERROR = str(e)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Fake News Detection System",
    page_icon="📰",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #777;
        font-size: 18px;
        margin-bottom: 30px;
    }

    .result-box {
        padding: 20px;
        border-radius: 12px;
        margin-top: 15px;
        text-align: center;
        border: 1px solid #ddd;
    }

    .result-title {
        font-size: 30px;
        font-weight: 700;
    }

    .metric-box {
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #ddd;
        text-align: center;
        min-height: 110px;
    }

    .metric-title {
        font-size: 15px;
        color: #777;
    }

    .metric-value {
        font-size: 25px;
        font-weight: 700;
        margin-top: 5px;
    }

    .evidence-card {
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin-bottom: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">📰 Fake News Detection System</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Machine Learning + External Evidence Verification'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# IMPORT ERROR
# ============================================================

if IMPORT_ERROR:

    st.error(
        "Unable to load the V2 verification pipeline."
    )

    st.code(IMPORT_ERROR)

    st.stop()


# ============================================================
# INPUT SECTION
# ============================================================

st.subheader("Enter News")

headline = st.text_input(
    "News Headline",
    placeholder="Enter the news headline..."
)

article = st.text_area(
    "News Article",
    placeholder="Enter the complete news article or claim...",
    height=220
)


# ============================================================
# ANALYZE BUTTON
# ============================================================

analyze = st.button(
    "🔍 Analyze News",
    type="primary",
    use_container_width=True
)


# ============================================================
# ANALYSIS
# ============================================================

if analyze:

    if not headline.strip():

        st.warning(
            "Please enter a news headline."
        )

        st.stop()

    if not article.strip():

        st.warning(
            "Please enter the news article."
        )

        st.stop()

    # --------------------------------------------------------
    # PROGRESS
    # --------------------------------------------------------

    progress = st.progress(0)

    status = st.empty()

    # --------------------------------------------------------
    # ML
    # --------------------------------------------------------

    status.info(
        "Step 1/5 — Running machine learning prediction..."
    )

    try:

        ml_label, ml_confidence = ml_prediction(
            headline.strip(),
            article.strip()
        )

    except Exception as e:

        progress.empty()
        status.empty()

        st.error(
            f"ML prediction failed:\n\n{e}"
        )

        st.stop()

    progress.progress(20)

    # --------------------------------------------------------
    # EXTERNAL EVIDENCE
    # --------------------------------------------------------

    status.info(
        "Step 2/5 — Searching external evidence..."
    )

    try:

        evidence = collect_evidence(
            headline.strip(),
            article.strip()
        )

    except Exception as e:

        progress.empty()
        status.empty()

        st.error(
            f"Evidence search failed:\n\n{e}"
        )

        st.stop()

    progress.progress(50)

    # --------------------------------------------------------
    # EVIDENCE SCORING
    # --------------------------------------------------------

    status.info(
        "Step 3/5 — Scoring evidence relevance..."
    )

    evidence_result = calculate_final_evidence(
        evidence
    )

    progress.progress(70)

    # --------------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------------

    status.info(
        "Step 4/5 — Comparing evidence with claim..."
    )

    final_assessment, final_confidence = (
        calculate_final_decision(
            ml_label,
            ml_confidence,
            evidence_result
        )
    )

    progress.progress(90)

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    status.success(
        "Step 5/5 — Analysis completed."
    )

    progress.progress(100)

    # ========================================================
    # RESULTS
    # ========================================================

    st.divider()

    st.subheader("Final Assessment")

    if final_assessment == "REAL":

        st.success(
            f"### ✅ REAL\n\n"
            f"Confidence: {final_confidence * 100:.2f}%"
        )

    elif final_assessment == "FAKE":

        st.error(
            f"### ❌ FAKE\n\n"
            f"Confidence: {final_confidence * 100:.2f}%"
        )

    else:

        st.warning(
            f"### ⚠️ NEEDS VERIFICATION\n\n"
            f"Confidence: {final_confidence * 100:.2f}%"
        )


    # ========================================================
    # METRICS
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "ML Prediction",
            ml_label
        )

    with col2:

        st.metric(
            "ML Confidence",
            f"{ml_confidence * 100:.2f}%"
        )

    with col3:

        st.metric(
            "Evidence Assessment",
            evidence_result["assessment"]
        )

    with col4:

        st.metric(
            "Evidence Score",
            f"{evidence_result['score'] * 100:.2f}%"
        )


    # ========================================================
    # EVIDENCE LEVEL
    # ========================================================

    st.subheader("Evidence Strength")

    level = evidence_result["level"]

    if level == "STRONG":

        st.success(
            f"Evidence Level: **{level}**"
        )

    elif level == "MODERATE":

        st.warning(
            f"Evidence Level: **{level}**"
        )

    else:

        st.info(
            f"Evidence Level: **{level}**"
        )


    # ========================================================
    # STATISTICS
    # ========================================================

    st.subheader("Verification Statistics")

    total_evidence = len(evidence)

    article_content = sum(
        e["type"] == "ARTICLE_CONTENT"
        for e in evidence
    )

    rss_summary = sum(
        e["type"] == "RSS_SUMMARY"
        for e in evidence
    )

    trusted_sources = sum(
        e["trusted"]
        for e in evidence
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Evidence Found",
            total_evidence
        )

    with col2:

        st.metric(
            "Article Content",
            article_content
        )

    with col3:

        st.metric(
            "RSS Results",
            rss_summary
        )

    with col4:

        st.metric(
            "Trusted Sources",
            trusted_sources
        )


    # ========================================================
    # SUPPORT / CONTRADICTION
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Strong Supporting",
            evidence_result[
                "strong_supporting"
            ]
        )

    with col2:

        st.metric(
            "Strong Contradicting",
            evidence_result[
                "strong_contradicting"
            ]
        )

    with col3:

        st.metric(
            "Trusted Supporting",
            evidence_result[
                "trusted_supporting"
            ]
        )

    with col4:

        st.metric(
            "Trusted Contradicting",
            evidence_result[
                "trusted_contradicting"
            ]
        )


    # ========================================================
    # EVIDENCE
    # ========================================================

    st.divider()

    st.subheader("🔎 External Evidence")

    if not evidence:

        st.info(
            "No useful external evidence was found."
        )

    else:

        for i, e in enumerate(
            evidence,
            start=1
        ):

            with st.expander(
                f"{i}. {e['title']}"
            ):

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"**Source:** {e['source']}"
                    )

                    st.write(
                        f"**Type:** {e['type']}"
                    )

                    st.write(
                        f"**Relationship:** "
                        f"{e['relationship']}"
                    )

                    st.write(
                        f"**Trusted Source:** "
                        f"{'YES' if e['trusted'] else 'NO'}"
                    )

                with col2:

                    st.write(
                        f"**Quality:** "
                        f"{e['quality'] * 100:.2f}%"
                    )

                    st.write(
                        f"**Relevance:** "
                        f"{e['relevance'] * 100:.2f}%"
                    )

                    st.write(
                        f"**Claim Overlap:** "
                        f"{e['claim_overlap'] * 100:.2f}%"
                    )

                    st.write(
                        f"**Entity Overlap:** "
                        f"{e['entity_overlap'] * 100:.2f}%"
                    )

                st.write(
                    f"**Event Overlap:** "
                    f"{e['event_overlap'] * 100:.2f}%"
                )

                st.write(
                    f"**Year Match:** "
                    f"{e['year_match'] * 100:.2f}%"
                )

                st.write(
                    f"**Supporting:** "
                    f"{e['supporting']}"
                )

                st.write(
                    f"**Contradicting:** "
                    f"{e['contradicting']}"
                )

                if e["entities"]:

                    st.write(
                        "**Entities:** "
                        + ", ".join(e["entities"])
                    )

                if e["events"]:

                    st.write(
                        "**Events:** "
                        + ", ".join(e["events"])
                    )

                st.markdown(
                    f"[🔗 Open Source]({e['link']})"
                )


    # ========================================================
    # INTERPRETATION
    # ========================================================

    st.divider()

    st.subheader("📊 System Interpretation")

    if final_assessment == "REAL":

        st.write(
            "The machine-learning model and external "
            "evidence were evaluated together. The "
            "available evidence strongly supports the claim."
        )

    elif final_assessment == "FAKE":

        st.write(
            "The external evidence contains strong "
            "contradictory information. The claim should "
            "be treated as false."
        )

    else:

        st.write(
            "The available evidence was insufficient to "
            "confirm or contradict the claim. The system "
            "therefore recommends further verification."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Fake News Detection System — "
    "NLP + Machine Learning + External Evidence Verification"
)