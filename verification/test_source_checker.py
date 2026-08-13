from source_checker import check_source


urls = [
    "https://www.nasa.gov/example",
    "https://www.ndtv.com/example",
    "https://example.com/news"
]


for url in urls:
    result = check_source(url)

    print("\nURL:", url)
    print("Domain:", result["domain"])
    print("Credibility:", result["credibility"])