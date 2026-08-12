from system_layer.project_indexer import search_code

query = "ask_ai"

results = search_code(".", query)

print(f"\nSearch Results for '{query}'\n")

if not results:
    print("No results found.")
else:
    for result in results:
        print("=" * 70)
        print(f"File : {result['file']}")
        print(f"Line : {result['line']}")
        print(f"Code : {result['snippet']}")
        print()