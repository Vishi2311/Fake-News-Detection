import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# Load V2 model and vectorizer
model = joblib.load(
    "models/v2/v2_calibrated_fake_news_model.pkl"
)

vectorizer = joblib.load(
    "models/v2/v2_tfidf_vectorizer.pkl"
)


def predict_news(news):
    news_tfidf = vectorizer.transform([news])

    prediction = model.predict(news_tfidf)[0]
    probabilities = model.predict_proba(news_tfidf)[0]

    if prediction == 0:
        result = "FAKE"
        confidence = probabilities[0] * 100
    else:
        result = "REAL"
        confidence = probabilities[1] * 100

    return prediction, result, confidence


def evaluate_external_dataset(file_path):
    df = pd.read_csv(file_path)

    df["content"] = (
        df["title"].fillna("").astype(str)
        + " "
        + df["text"].fillna("").astype(str)
    )

    predictions = []
    confidences = []

    for news in df["content"]:
        prediction, result, confidence = predict_news(news)

        predictions.append(prediction)
        confidences.append(confidence)

    df["predicted_label"] = predictions
    df["confidence"] = confidences

    y_true = df["actual_label"]
    y_pred = df["predicted_label"]

    print("\n========================================")
    print("V2 EXTERNAL TEST RESULTS")
    print("========================================")

    print("\nArticles tested:", len(df))

    print("\nAccuracy:",
          f"{accuracy_score(y_true, y_pred) * 100:.2f}%")

    print("\nPrecision:",
          f"{precision_score(y_true, y_pred) * 100:.2f}%")

    print("Recall:",
          f"{recall_score(y_true, y_pred) * 100:.2f}%")

    print("F1 Score:",
          f"{f1_score(y_true, y_pred) * 100:.2f}%")

    print("\nClassification Report:")
    print(classification_report(
        y_true,
        y_pred,
        target_names=["Fake", "Real"]
    ))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_true, y_pred))

    print("\nIndividual Predictions:")
    print(
        df[
            [
                "title",
                "actual_label",
                "predicted_label",
                "confidence",
                "source"
            ]
        ].to_string(index=False)
    )

    return df


if __name__ == "__main__":

    evaluate_external_dataset(
        "data/processed/external_test.csv"
    )