import joblib


# Load saved model and vectorizer
model = joblib.load("models/calibrated_fake_news_model.pkl")
vectorizer = joblib.load("models/tfidf_vectorizer.pkl")

def predict_news(news):
    """
    Predict whether a news article is fake or real
    and return the model's confidence.
    """

    news_tfidf = vectorizer.transform([news])

    prediction = model.predict(news_tfidf)[0]
    probabilities = model.predict_proba(news_tfidf)[0]

    if prediction == 0:
        result = "FAKE"
        confidence = probabilities[0] * 100
    else:
        result = "REAL"
        confidence = probabilities[1] * 100

    return result, confidence


if __name__ == "__main__":

    title = input("Enter news title: ")

    article = input("Enter news article: ")

    news = title + " " + article

    result, confidence = predict_news(news)

    print("\n-------------------------")
    print("Prediction:", result)
    print(f"Confidence: {confidence:.2f}%")
    print("-------------------------")