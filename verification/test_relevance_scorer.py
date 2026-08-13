from relevance_scorer import calculate_relevance


claim = "NASA announces new lunar mission"


evidence_titles = [
    "NASA announces new lunar mission",
    "NASA plans new mission to the Moon",
    "India discusses space exploration",
    "Weather forecast for Delhi"
]


print("\n==============================")
print("RELEVANCE TEST")
print("==============================")


for title in evidence_titles:

    score = calculate_relevance(
        claim,
        title
    )

    print("\nEvidence:")
    print(title)

    print("Relevance Score:", score)