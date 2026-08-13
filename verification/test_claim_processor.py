from claim_processor import prepare_claim


title = "Government announces new education policy"

article = """
The government has announced a new education policy
that will introduce several changes to schools and universities.
"""

result = prepare_claim(title, article)

print("TITLE:")
print(result["title"])

print("\nARTICLE:")
print(result["article"])

print("\nCOMBINED TEXT:")
print(result["combined_text"])

print("\nSEARCH QUERY:")
print(result["search_query"])