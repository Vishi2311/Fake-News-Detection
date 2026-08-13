from evidence_comparator import compare_evidence


claim = "NASA announces new lunar mission"


evidence = [
    {
        "title": "NASA announces plans for a new lunar mission",
        "source": "nasa.gov",
        "link": "https://www.nasa.gov/example"
    },
    {
        "title": "New lunar mission planned by NASA",
        "source": "reuters.com",
        "link": "https://www.reuters.com/example"
    },
    {
        "title": "NASA lunar mission receives international attention",
        "source": "ndtv.com",
        "link": "https://www.ndtv.com/example"
    }
]


result = compare_evidence(claim, evidence)


print("\nCLAIM:")
print(claim)

print("\nASSESSMENT:")
print(result["assessment"])

print("\nSUPPORTING EVIDENCE:")
for item in result["supporting"]:
    print("-", item["title"])

print("\nCONTRADICTING EVIDENCE:")
for item in result["contradicting"]:
    print("-", item["title"])