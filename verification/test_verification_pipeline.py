from verification_pipeline import verify_news


title = "NASA announces new lunar mission"
article = "NASA has announced plans for a new mission to the Moon."


result = verify_news(
    title,
    article,
    max_results=5
)


print("\n==============================")
print("NEWS VERIFICATION RESULT")
print("==============================")

print("\nClaim:")
print(title)

print("\nAssessment:")
print(result["assessment"])

print("\nEvidence Score:")
print(
    result["evidence_score"]["score"],
    "%"
)

print("\nEvidence Level:")
print(
    result["evidence_score"]["level"]
)

print("\nEvidence Found:")
print(len(result["evidence"]))

print("\nSources:")

for item in result["evidence"]:

    print("\nTitle:")
    print(item.get("title", ""))

    print("Source:")
    print(item.get("source", ""))

    print("Credibility:")
    print(item.get("credibility", "Unknown"))

    print("Relevance Score:")
    print(item.get("relevance_score", 0))

    print("Link:")
    print(item.get("link", ""))