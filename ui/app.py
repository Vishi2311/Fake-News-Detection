import streamlit as st
import psycopg2
import os
import sys
from dotenv import load_dotenv


# =========================================================
# PROJECT PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

VERIFICATION_DIR = os.path.join(
    BASE_DIR,
    "verification"
)

if VERIFICATION_DIR not in sys.path:
    sys.path.insert(0, VERIFICATION_DIR)


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv(
    os.path.join(
        BASE_DIR,
        ".env"
    )
)


# =========================================================
# V2.1 PIPELINE
# =========================================================

try:

    from v2_1_full_pipeline import (
        ml_prediction,
        collect_evidence,
        calculate_final_evidence,
        calculate_final_decision
    )

    V2_AVAILABLE = True
    V2_ERROR = None

except Exception as e:

    V2_AVAILABLE = False
    V2_ERROR = str(e)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Fake News Detection",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    /* Main title */
    .main-title {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        margin-top: 10px;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        margin-bottom: 25px;
    }

    /* Verdict cards */
    .verdict {
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin: 10px 0;
    }

    .verdict-title {
        font-size: 30px;
        font-weight: 800;
    }

    .verdict-confidence {
        font-size: 20px;
        margin-top: 8px;
    }

    /* Source cards */
    .source-card {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dddddd;
        margin-bottom: 10px;
    }

    /* Small labels */
    .section-note {
        font-size: 14px;
        margin-bottom: 10px;
    }

    /* Footer */
    .footer {
        text-align: center;
        font-size: 13px;
        margin-top: 40px;
        padding: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# DATABASE
# =========================================================

def get_connection():

    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )


def save_prediction(
    title,
    prediction,
    confidence
):

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO predictions
            (title, prediction, confidence)
            VALUES (%s, %s, %s)
            """,
            (
                title,
                prediction,
                float(confidence)
            )
        )

        connection.commit()

        return True, None

    except Exception as e:

        if connection:
            connection.rollback()

        return False, str(e)

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


def get_history():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                title,
                prediction,
                confidence,
                predicted_at
            FROM predictions
            ORDER BY predicted_at DESC
            LIMIT 20
            """
        )

        rows = cursor.fetchall()

        return rows, None

    except Exception as e:

        return [], str(e)

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# RESULT NORMALIZATION
# =========================================================

def normalize_ml_result(result):

    label = None
    confidence = None

    if isinstance(result, dict):

        label = (
            result.get("label")
            or result.get("prediction")
            or result.get("ml_prediction")
            or result.get("result")
        )

        confidence = (
            result.get("confidence")
            or result.get("ml_confidence")
        )

    elif isinstance(result, (tuple, list)):

        if len(result) >= 1:
            label = result[0]

        if len(result) >= 2:
            confidence = result[1]

    else:

        label = result

    if label is not None:

        label = str(label).upper()

        if label in ["0", "FALSE"]:
            label = "FAKE"

        elif label in ["1", "TRUE"]:
            label = "REAL"

    if confidence is not None:

        confidence = float(confidence)

        if confidence <= 1:
            confidence *= 100

    return label, confidence


def normalize_final_result(result):

    assessment = None
    confidence = None

    if isinstance(result, dict):

        assessment = (
            result.get("assessment")
            or result.get("final_assessment")
            or result.get("final")
            or result.get("decision")
        )

        confidence = (
            result.get("confidence")
            or result.get("final_confidence")
        )

    elif isinstance(result, (tuple, list)):

        if len(result) >= 1:
            assessment = result[0]

        if len(result) >= 2:
            confidence = result[1]

    else:

        assessment = result

    if assessment is not None:
        assessment = str(assessment).upper()

    if confidence is not None:

        confidence = float(confidence)

        if confidence <= 1:
            confidence *= 100

    return assessment, confidence


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">'
    '📰 Fake News Detection Using ML & NLP'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Machine Learning + Natural Language Processing + '
    'External Evidence Verification'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("🔧 System")

    if V2_AVAILABLE:
        st.success("V2.1 Pipeline Ready")
    else:
        st.error("V2.1 Pipeline Error")

    model_exists = os.path.exists(
        os.path.join(
            BASE_DIR,
            "models",
            "calibrated_fake_news_model.pkl"
        )
    )

    vectorizer_exists = os.path.exists(
        os.path.join(
            BASE_DIR,
            "models",
            "tfidf_vectorizer.pkl"
        )
    )

    if model_exists:
        st.success("ML Model Available")
    else:
        st.error("ML Model Missing")

    if vectorizer_exists:
        st.success("TF-IDF Vectorizer Available")
    else:
        st.error("TF-IDF Vectorizer Missing")

    st.success("PostgreSQL Enabled")

    st.divider()

    st.header("🧠 How It Works")

    st.write(
        """
        **1. ML Prediction**

        The news is processed using TF-IDF
        and the trained classification model.

        **2. Evidence Retrieval**

        External news sources are searched
        for relevant evidence.

        **3. Evidence Analysis**

        Sources are evaluated using relevance,
        entity overlap, event overlap, quality
        and source trust.

        **4. Final Decision**

        ML prediction and evidence assessment
        are combined to produce the final result.
        """
    )

    st.divider()

    st.caption(
        "Fake News Detection Project"
    )


if not V2_AVAILABLE:

    st.error(
        "The V2.1 verification pipeline could not be loaded."
    )

    st.code(V2_ERROR)

    st.stop()


# =========================================================
# SYSTEM STATUS
# =========================================================

st.subheader("⚙️ System Status")

status1, status2, status3 = st.columns(3)

with status1:
    st.success("✅ V2.1 Pipeline Ready")

with status2:
    st.success("✅ ML Model Available")

with status3:
    st.success("🗄️ PostgreSQL Connected")


st.divider()


# =========================================================
# NEWS INPUT
# =========================================================

st.header("📝 Analyze News")

st.markdown(
    "Enter a headline and/or article below. "
    "The system will classify the news and verify it "
    "using external evidence."
)

title = st.text_input(
    "News Headline",
    placeholder="Example: NASA successfully launched a new spacecraft"
)

article = st.text_area(
    "News Article",
    placeholder="Paste the complete news article here...",
    height=220
)

check_news = st.button(
    "🔍 Analyze News",
    type="primary",
    use_container_width=True
)


# =========================================================
# ANALYSIS
# =========================================================

if check_news:

    if not title.strip() and not article.strip():

        st.warning(
            "⚠️ Please enter a news headline or article."
        )

        st.stop()

    progress = st.progress(0)
    status = st.empty()

    try:

        # =================================================
        # STEP 1 — ML
        # =================================================

        status.info(
            "🤖 Step 1/5 — Running machine learning prediction..."
        )

        progress.progress(10)

        ml_raw = ml_prediction(
            title.strip(),
            article.strip()
        )

        ml_result, ml_confidence = normalize_ml_result(
            ml_raw
        )

        progress.progress(25)


        # =================================================
        # STEP 2 — EVIDENCE
        # =================================================

        status.info(
            "🌐 Step 2/5 — Searching external evidence..."
        )

        evidence = collect_evidence(
            title.strip(),
            article.strip()
        )

        progress.progress(50)


        # =================================================
        # STEP 3
        # =================================================

        status.info(
            "🔎 Step 3/5 — Scoring evidence relevance..."
        )

        progress.progress(60)


        # =================================================
        # STEP 4
        # =================================================

        status.info(
            "⚖️ Step 4/5 — Comparing evidence with claim..."
        )

        progress.progress(75)


        # =================================================
        # STEP 5
        # =================================================

        status.info(
            "📊 Step 5/5 — Calculating final assessment..."
        )

        evidence_result = calculate_final_evidence(
            evidence
        )

        progress.progress(90)


        # =================================================
        # FINAL DECISION
        # =================================================

        final_raw = calculate_final_decision(
            ml_result,
            ml_confidence,
            evidence_result
        )

        final_assessment, final_confidence = (
            normalize_final_result(
                final_raw
            )
        )

        progress.progress(100)

        status.success(
            "✅ Analysis completed successfully."
        )


        # =================================================
        # SAVE RESULT
        # =================================================

        database_confidence = (
            final_confidence
            if final_confidence is not None
            else ml_confidence
        )

        if (
            final_assessment in ["REAL", "FAKE", "NEEDS VERIFICATION"]
            and database_confidence is not None
        ):

            saved, db_error = save_prediction(
                title.strip(),
                final_assessment,
                database_confidence
            )

            if saved:

                st.success(
                    "💾 Prediction successfully saved to PostgreSQL."
                )

            else:

                st.warning(
                    "⚠️ Prediction generated, but "
                    "could not be saved to PostgreSQL."
                )

                st.code(db_error)


        # =================================================
        # RESULTS
        # =================================================

        st.divider()

        st.header("📊 News Analysis Results")


        # =================================================
        # ML CARD
        # =================================================

        st.subheader("🤖 Machine Learning Prediction")

        ml_col1, ml_col2 = st.columns(2)

        with ml_col1:

            if ml_result == "FAKE":

                st.error(
                    "🚨 ML Prediction: FAKE"
                )

            elif ml_result == "REAL":

                st.success(
                    "✅ ML Prediction: REAL"
                )

            else:

                st.warning(
                    f"ML Prediction: {ml_result}"
                )

        with ml_col2:

            if ml_confidence is not None:

                st.metric(
                    "ML Confidence",
                    f"{ml_confidence:.2f}%"
                )

                st.progress(
                    min(
                        max(
                            ml_confidence / 100,
                            0.0
                        ),
                        1.0
                    )
                )


        # =================================================
        # EVIDENCE CARD
        # =================================================

        st.divider()

        st.subheader(
            "🌐 External Evidence Verification"
        )

        evidence_assessment = evidence_result.get(
            "assessment",
            "INCONCLUSIVE"
        )

        evidence_score = float(
            evidence_result.get(
                "score",
                0.0
            )
        )

        evidence_level = evidence_result.get(
            "level",
            "WEAK"
        )

        ev1, ev2, ev3 = st.columns(3)

        with ev1:

            st.metric(
                "Assessment",
                evidence_assessment
            )

        with ev2:

            st.metric(
                "Evidence Score",
                f"{evidence_score * 100:.2f}%"
            )

        with ev3:

            st.metric(
                "Evidence Level",
                evidence_level
            )

        st.progress(
            min(
                max(
                    evidence_score,
                    0.0
                ),
                1.0
            )
        )


        # =================================================
        # FINAL VERDICT
        # =================================================

        st.divider()

        st.header("🎯 Final System Assessment")

        if final_assessment == "REAL":

            st.success(
                "## ✅ FINAL ASSESSMENT: REAL"
            )

        elif final_assessment == "FAKE":

            st.error(
                "## 🚨 FINAL ASSESSMENT: FAKE"
            )

        else:

            st.warning(
                "## ⚠️ FINAL ASSESSMENT: NEEDS VERIFICATION"
            )

        if final_confidence is not None:

            st.metric(
                "Final Confidence",
                f"{final_confidence:.2f}%"
            )

            st.progress(
                min(
                    max(
                        final_confidence / 100,
                        0.0
                    ),
                    1.0
                )
            )


        # =================================================
        # DECISION EXPLANATION
        # =================================================

        st.subheader("💡 Decision Explanation")

        if (
            ml_result == "FAKE"
            and evidence_assessment == "SUPPORTED"
        ):

            st.info(
                "The ML model classified the news as FAKE, "
                "but external evidence supports the claim. "
                "The final decision therefore considers the "
                "external evidence."
            )

        elif (
            ml_result == "REAL"
            and evidence_assessment == "CONTRADICTED"
        ):

            st.warning(
                "The ML model classified the news as REAL, "
                "but external evidence contradicts the claim. "
                "The final decision considers the contradictory evidence."
            )

        elif evidence_assessment == "INCONCLUSIVE":

            st.warning(
                "The ML model produced a prediction, but the "
                "retrieved external evidence was not strong "
                "enough to confirm or contradict the claim. "
                "Therefore, the system recommends further verification."
            )

        elif evidence_assessment == "SUPPORTED":

            st.success(
                "External evidence supports the submitted claim."
            )

        elif evidence_assessment == "CONTRADICTED":

            st.error(
                "External evidence contradicts the submitted claim."
            )

        else:

            st.info(
                "The final assessment was generated by combining "
                "the machine learning result and external evidence."
            )


        # =================================================
        # EVIDENCE STATISTICS
        # =================================================

        st.divider()

        st.subheader("📊 Evidence Statistics")

        total_evidence = (
            len(evidence)
            if isinstance(evidence, list)
            else 0
        )

        strong_supporting = evidence_result.get(
            "strong_supporting",
            0
        )

        strong_contradicting = evidence_result.get(
            "strong_contradicting",
            0
        )

        trusted_supporting = evidence_result.get(
            "trusted_supporting",
            0
        )

        trusted_contradicting = evidence_result.get(
            "trusted_contradicting",
            0
        )

        s1, s2, s3, s4 = st.columns(4)

        with s1:

            st.metric(
                "Evidence Found",
                total_evidence
            )

        with s2:

            st.metric(
                "Strong Supporting",
                strong_supporting
            )

        with s3:

            st.metric(
                "Strong Contradicting",
                strong_contradicting
            )

        with s4:

            st.metric(
                "Trusted Supporting",
                trusted_supporting
            )

        st.write(
            f"**Trusted Contradicting:** "
            f"{trusted_contradicting}"
        )


        # =================================================
        # EVIDENCE SOURCES
        # =================================================

        st.divider()

        st.subheader(
            f"📚 Evidence Sources ({total_evidence})"
        )

        if evidence:

            for index, item in enumerate(
                evidence,
                start=1
            ):

                supporting = item.get(
                    "supporting",
                    False
                )

                contradicting = item.get(
                    "contradicting",
                    False
                )

                if supporting:

                    icon = "✅"

                elif contradicting:

                    icon = "❌"

                else:

                    icon = "ℹ️"

                source_title = item.get(
                    "title",
                    "Untitled Evidence"
                )

                with st.expander(
                    f"{icon} {index}. {source_title}"
                ):

                    source_col1, source_col2 = (
                        st.columns(2)
                    )

                    with source_col1:

                        st.write(
                            "**Source:** "
                            + str(
                                item.get(
                                    "source",
                                    "Unknown"
                                )
                            )
                        )

                        st.write(
                            "**Publisher:** "
                            + str(
                                item.get(
                                    "publisher",
                                    "Unknown"
                                )
                            )
                        )

                        st.write(
                            "**Type:** "
                            + str(
                                item.get(
                                    "type",
                                    "Unknown"
                                )
                            )
                        )

                        st.write(
                            "**Relationship:** "
                            + str(
                                item.get(
                                    "relationship",
                                    "UNKNOWN"
                                )
                            )
                        )

                    with source_col2:

                        st.write(
                            "**Relevance:** "
                            f"{item.get('relevance', 0) * 100:.2f}%"
                        )

                        st.write(
                            "**Claim Overlap:** "
                            f"{item.get('claim_overlap', 0) * 100:.2f}%"
                        )

                        st.write(
                            "**Entity Overlap:** "
                            f"{item.get('entity_overlap', 0) * 100:.2f}%"
                        )

                        st.write(
                            "**Event Overlap:** "
                            f"{item.get('event_overlap', 0) * 100:.2f}%"
                        )

                    st.write(
                        "**Year Match:** "
                        f"{item.get('year_match', 0) * 100:.2f}%"
                    )

                    st.write(
                        "**Quality:** "
                        f"{item.get('quality', 0) * 100:.2f}%"
                    )

                    st.write(
                        "**Trust Score:** "
                        f"{item.get('trust_score', 0) * 100:.2f}%"
                    )

                    trusted = item.get(
                        "trusted",
                        False
                    )

                    if trusted:

                        st.success(
                            "🛡️ Trusted Source"
                        )

                    else:

                        st.info(
                            "Source not classified as trusted"
                        )

                    link = item.get(
                        "link",
                        ""
                    )

                    if link:

                        st.markdown(
                            f"[🔗 Open Original Source]({link})"
                        )

        else:

            st.info(
                "No external evidence was found."
            )


    except Exception as e:

        status.error(
            "❌ Analysis failed."
        )

        st.error(
            "An error occurred while processing the news."
        )

        st.exception(e)


# =========================================================
# PREDICTION HISTORY
# =========================================================

st.divider()

st.header("📜 Prediction History")

with st.expander(
    "View Last 20 Predictions"
):

    rows, error = get_history()

    if error:

        st.error(
            "Could not load prediction history."
        )

        st.code(error)

    elif not rows:

        st.info(
            "No prediction history available yet."
        )

    else:

        for row in rows:

            prediction_id = row[0]
            prediction_title = row[1]
            prediction_result = row[2]
            prediction_confidence = row[3]
            prediction_time = row[4]

            st.write(
                f"**#{prediction_id} — "
                f"{prediction_title}**"
            )

            if prediction_result == "FAKE":

                st.error(
                    f"🚨 FAKE — "
                    f"Confidence: "
                    f"{float(prediction_confidence):.2f}%"
                )

            elif prediction_result == "REAL":

                st.success(
                    f"✅ REAL — "
                    f"Confidence: "
                    f"{float(prediction_confidence):.2f}%"
                )

            elif prediction_result == "NEEDS VERIFICATION":

                st.warning(
                    f"⚠️ NEEDS VERIFICATION — "
                    f"Confidence: "
                    f"{float(prediction_confidence):.2f}%"
                )

            else:

                st.info(
                    f"ℹ️ {prediction_result} — "
                    f"Confidence: "
                    f"{float(prediction_confidence):.2f}%"
                )

            st.caption(
                f"Predicted at: {prediction_time}"
            )

            st.divider()


# =========================================================
# ABOUT
# =========================================================

st.divider()

with st.expander(
    "ℹ️ About This Project"
):

    st.write(
        """
        ### Fake News Detection Using ML & NLP

        This project combines Machine Learning,
        Natural Language Processing, external evidence
        retrieval and source credibility analysis.

        **Machine Learning**

        The system uses TF-IDF text representation and
        a calibrated classification model to classify
        news as REAL or FAKE.

        **External Evidence Verification**

        The system searches external news sources and
        evaluates evidence using factors such as:

        • Relevance
        • Claim overlap
        • Entity overlap
        • Event overlap
        • Year matching
        • Source quality
        • Source trust

        **Final Assessment**

        The system can produce three final outcomes:

        • REAL
        • FAKE
        • NEEDS VERIFICATION

        When evidence is inconclusive, the system does
        not automatically treat the ML prediction as
        the final truth.

        **Database**

        Prediction results are stored in PostgreSQL
        for historical analysis.
        """
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    '<div class="footer">'
    'Fake News Detection System • '
    'Machine Learning + NLP + Evidence Verification'
    '</div>',
    unsafe_allow_html=True
)