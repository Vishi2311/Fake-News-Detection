import streamlit as st
import joblib
import psycopg2
import os
from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# LOAD MODEL AND TF-IDF VECTORIZER
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
# SAVE PREDICTION TO POSTGRESQL
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
# GET PREDICTION HISTORY
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
    page_title="Fake News Detector",
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
    '<div class="main-title">📰 Fake News Detection System</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Machine Learning Based News Classification'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# INPUT SECTION
# =========================================================

st.subheader("Enter News")

title = st.text_input(
    "News Title",
    placeholder="Enter the news headline..."
)

article = st.text_area(
    "News Article",
    placeholder="Paste the complete news article here...",
    height=250
)


# =========================================================
# PREDICTION
# =========================================================

if st.button("🔍 Detect News", use_container_width=True):

    if not title.strip() and not article.strip():

        st.warning("⚠️ Please enter a news title or article.")

    else:

        # Combine title and article
        news = title + " " + article

        # Convert text into TF-IDF features
        news_tfidf = vectorizer.transform([news])

        # Make prediction
        prediction = model.predict(news_tfidf)[0]

        # Get probabilities
        probabilities = model.predict_proba(news_tfidf)[0]

        # Determine result
        if prediction == 0:

            result = "FAKE"
            confidence = float(probabilities[0] * 100)

        else:

            result = "REAL"
            confidence = float(probabilities[1] * 100)


        # =================================================
        # DISPLAY RESULT
        # =================================================

        st.divider()

        st.subheader("Prediction Result")

        if result == "FAKE":

            st.error("🚨 Prediction: FAKE")

        else:

            st.success("✅ Prediction: REAL")


        # Confidence
        st.metric(
            label="Model Confidence",
            value=f"{confidence:.2f}%"
        )

        st.progress(
            int(confidence),
            text=f"Confidence: {confidence:.2f}%"
        )


        # =================================================
        # INTERPRETATION
        # =================================================

        if confidence >= 90:

            st.info(
                "The model is highly confident in this prediction."
            )

        elif confidence >= 70:

            st.info(
                "The model has relatively high confidence "
                "in this prediction."
            )

        else:

            st.warning(
                "The model has lower confidence. Consider "
                "verifying the information using reliable sources."
            )


        # =================================================
        # SAVE TO POSTGRESQL
        # =================================================

        saved, error = save_prediction(
            title,
            result,
            confidence
        )

        if saved:

            st.success(
                "✅ Prediction was successfully saved to PostgreSQL."
            )

        else:

            st.error(
                "❌ Prediction was made, but it could not be "
                "saved to PostgreSQL."
            )

            st.code(error)


# =========================================================
# PREDICTION HISTORY
# =========================================================

st.divider()

with st.expander("📊 Prediction History"):

    rows, error = get_history()

    if error:

        st.error("Could not load prediction history.")

        st.code(error)

    elif not rows:

        st.info("No prediction history available yet.")

    else:

        for row in rows:

            prediction_id = row[0]
            prediction_title = row[1]
            prediction_result = row[2]
            prediction_confidence = row[3]
            prediction_time = row[4]

            st.write(
                f"**#{prediction_id} — {prediction_title}**"
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
        This Fake News Detection System uses Natural Language
        Processing and Machine Learning to classify news articles
        as REAL or FAKE.

        The text is converted into numerical features using TF-IDF,
        and a calibrated LinearSVC model generates the prediction.

        The confidence score represents the model's estimated
        confidence, not a guarantee that the news is factually
        true or false.

        Prediction results are stored in PostgreSQL so that previous
        predictions can be viewed in the Prediction History section.
        """
    )