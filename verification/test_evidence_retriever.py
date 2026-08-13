from evidence_retriever import search_news


query = "NASA lunar mission"

results = search_news(query)

print("\nSEARCH QUERY:")
print(query)

print("\nEVIDENCE SOURCES:")

for i, result in enumerate(results, start=1):
    print(f"\n{i}. {result['title']}")
    print(f"Source: {result['source']}")
    print(f"Published: {result['published']}")
    print(f"Link: {result['link']}")