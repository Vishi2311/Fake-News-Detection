import streamlit as st
import joblib
import psycopg2
import os
from dotenv import load_dotenv

from verification.verification_pipeline import verify_news


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "..",
    "models",
    "calibrated_fake_news_model.pkl"
)

VECTORIZER_PATH = os.path.join(
    BASE_DIR,
    "..",
    "models",
    "tfidf_vectorizer.pkl"
)


# =========================================================
# LOAD MODEL AND VECTORIZER
# =========================================================

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )


# =========================================================
# SAVE PREDICTION
# =========================================================

def save_prediction(title, prediction, confidence):

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


# =========================================================
# GET HISTORY
# =========================================================

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
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Fake News Detection System",
    page_icon="📰",
    layout="centered"
)


# =========================================================
# CUSTOM CSS
# =========================================================

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
        font-size: 18px;
        margin-bottom: 30px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🔎 Fake News Detection & Verification</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Machine Learning Based News Classification with Evidence Verification'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# INPUT
# =========================================================

st.subheader("Enter News")

title = st.text_input(
    "News Headline",
    placeholder="Enter the news headline..."
)

article = st.text_area(
    "News Article",
    placeholder="Paste the news article here...",
    height=250
)


# =========================================================
# CHECK NEWS
# =========================================================

if st.button("🔍 Check News", use_container_width=True):

    if not title.strip() and not article.strip():

        st.warning(
            "⚠️ Please enter a news headline or article."
        )

    else:

        # =================================================
        # 1. MACHINE LEARNING PREDICTION
        # =================================================

        news = title + " " + article

        news_tfidf = vectorizer.transform([news])

        prediction = model.predict(news_tfidf)[0]

        probabilities = model.predict_proba(news_tfidf)[0]

        if prediction == 0:

            ml_result = "FAKE"
            confidence = float(probabilities[0] * 100)

        else:

            ml_result = "REAL"
            confidence = float(probabilities[1] * 100)


        # =================================================
        # 2. EXTERNAL EVIDENCE VERIFICATION
        # =================================================

        try:

            verification_result = verify_news(
                title,
                article,
                max_results=5
            )

        except Exception as e:

            st.error(
                "❌ Evidence verification could not be completed."
            )

            st.code(str(e))

            verification_result = None


        # =================================================
        # 3. DISPLAY ML RESULT
        # =================================================

        st.divider()

        st.subheader("🤖 Machine Learning Prediction")

        if ml_result == "FAKE":

            st.error("🚨 Prediction: FAKE")

        else:

            st.success("✅ Prediction: REAL")

        st.metric(
            "Model Confidence",
            f"{confidence:.2f}%"
        )

        st.progress(
            min(int(confidence), 100),
            text=f"Confidence: {confidence:.2f}%"
        )


        # =================================================
        # MODEL INTERPRETATION
        # =================================================

        if confidence >= 90:

            st.info(
                "The machine learning model is highly confident "
                "in this prediction."
            )

        elif confidence >= 70:

            st.info(
                "The machine learning model has relatively high "
                "confidence in this prediction."
            )

        else:

            st.warning(
                "The model has lower confidence. External evidence "
                "should be considered carefully."
            )


        # =================================================
        # SAVE ML PREDICTION
        # =================================================

        saved, error = save_prediction(
            title,
            ml_result,
            confidence
        )

        if saved:

            st.success(
                "✅ Prediction saved to PostgreSQL."
            )

        else:

            st.warning(
                "⚠️ Prediction was made, but could not be "
                "saved to PostgreSQL."
            )


        # =================================================
        # 4. EVIDENCE VERIFICATION RESULT
        # =================================================

        if verification_result:

            st.divider()

            st.subheader("🌐 Evidence Verification")

            assessment = verification_result.get(
                "assessment",
                "INCONCLUSIVE"
            )

            evidence = verification_result.get(
                "evidence",
                []
            )

            # ---------------------------------------------
            # ASSESSMENT
            # ---------------------------------------------

            if assessment == "SUPPORTED":

                st.success(
                    "✅ Assessment: SUPPORTED"
                )

            elif assessment == "CONTRADICTED":

                st.error(
                    "❌ Assessment: CONTRADICTED"
                )

            else:

                st.warning(
                    "⚠️ Assessment: INCONCLUSIVE"
                )


            # ---------------------------------------------
            # EVIDENCE SCORE
            # ---------------------------------------------

            if evidence:

                # Recalculate using existing evidence scorer
                from verification.evidence_scorer import (
                    calculate_evidence_score
                )

                evidence_score = calculate_evidence_score(
                    evidence
                )

                score = evidence_score.get(
                    "score",
                    0
                )

                level = evidence_score.get(
                    "level",
                    "NO EVIDENCE"
                )

            else:

                score = 0
                level = "NO EVIDENCE"


            st.metric(
                "Evidence Score",
                f"{score:.1f}%"
            )

            st.write(
                f"**Evidence Level:** {level}"
            )

            st.write(
                f"**Evidence Found:** {len(evidence)}"
            )


            # =================================================
            # 5. EVIDENCE SOURCES
            # =================================================

            if evidence:

                st.subheader(
                    f"📚 Evidence Sources ({len(evidence)})"
                )

                for index, item in enumerate(
                    evidence,
                    start=1
                ):

                    with st.expander(
                        f"{index}. {item.get('title', 'Untitled')}"
                    ):

                        st.write(
                            f"**Source:** "
                            f"{item.get('source', 'Unknown')}"
                        )

                        st.write(
                            f"**Credibility:** "
                            f"{item.get('credibility', 'Unknown')}"
                        )

                        st.write(
                            f"**Relevance Score:** "
                            f"{item.get('relevance_score', 0):.2f}"
                        )

                        link = item.get(
                            "link",
                            ""
                        )

                        if link:

                            st.markdown(
                                f"[Open Source]({link})"
                            )


            else:

                st.info(
                    "No external evidence was found."
                )


# =========================================================
# PREDICTION HISTORY
# =========================================================

st.divider()

with st.expander("📊 Prediction History"):

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
                    f"🚨 FAKE — Confidence: "
                    f"{float(prediction_confidence):.2f}%"
                )

            else:

                st.success(
                    f"✅ REAL — Confidence: "
                    f"{float(prediction_confidence):.2f}%"
                )

            st.caption(
                f"Predicted at: {prediction_time}"
            )

            st.divider()


# =========================================================
# ABOUT PROJECT
# =========================================================

with st.expander("ℹ️ About this project"):

    st.write(
        """
        This Version 1 Fake News Detection System combines
        machine learning based news classification with
        external evidence verification.

        The machine learning component uses TF-IDF features
        and a calibrated classification model to predict
        whether a news article is REAL or FAKE.

        The verification component searches for external
        evidence, evaluates source credibility, calculates
        relevance, and produces an evidence-based assessment.

        The three possible verification assessments are:

        • SUPPORTED
        • CONTRADICTED
        • INCONCLUSIVE

        The evidence score indicates the strength of the
        retrieved evidence. It does not guarantee factual truth.

        Prediction results are stored in PostgreSQL.
        """
    )