from system_layer.code_analyzer import analyze_project

project = analyze_project(".")

for file in project:

    print("=" * 70)
    print(file["file"])

    print("\nFunctions:")

    for f in file["functions"]:
        print(
            f"  {f['name']} (Line {f['line']})"
        )

    print("\nClasses:")

    for c in file["classes"]:
        print(
            f"  {c['name']} (Line {c['line']})"
        )

    print("\nImports:")

    for i in file["imports"]:
        print(" ", i)

    print()