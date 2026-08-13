from evidence_scorer import calculate_evidence_score


evidence = [
    {
        "title": "NASA announces new lunar mission",
        "credibility": "Trusted",
        "relevance_score": 0.95
    },
    {
        "title": "NASA lunar mission plans",
        "credibility": "Trusted",
        "relevance_score": 0.90
    },
    {
        "title": "New lunar mission discussed",
        "credibility": "Unknown",
        "relevance_score": 0.70
    },
    {
        "title": "Moon exploration news",
        "credibility": "Unknown",
        "relevance_score": 0.60
    }
]


result = calculate_evidence_score(evidence)


print("\n==============================")
print("EVIDENCE SCORE")
print("==============================")

print("Score:", result["score"], "%")
print("Level:", result["level"])