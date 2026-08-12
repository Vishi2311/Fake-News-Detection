from predict import predict_news


test_cases = [
    {
        "title": "Government announces new infrastructure investment",
        "article": """
        Government officials announced a new infrastructure investment program
        focused on transportation and public services. The program is expected
        to begin next year following the completion of the planning process.
        """
    },
    {
        "title": "Scientists discover a magical plant that makes humans immortal",
        "article": """
        An anonymous website claims scientists have discovered a magical plant
        that can make humans live forever. No scientific institution has
        confirmed the claim.
        """
    },
    {
        "title": "Central bank announces interest rate decision",
        "article": """
        The central bank announced its latest interest rate decision after
        reviewing inflation, employment and economic growth data.
        """
    }
]


for i, item in enumerate(test_cases, start=1):

    news = item["title"] + " " + item["article"]

    result, confidence = predict_news(news)

    print(f"\nArticle {i}")
    print("Title:", item["title"])
    print("Prediction:", result)
    print(f"Confidence: {confidence:.2f}%")