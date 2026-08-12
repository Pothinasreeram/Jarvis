import ast
import os


def analyze_python_file(filepath):
    """
    Analyze a Python file and return:
    - Functions
    - Classes
    - Imports
    """

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except Exception:
        return None

    result = {
        "file": filepath,
        "functions": [],
        "classes": [],
        "imports": []
    }

    for node in ast.walk(tree):

        if isinstance(node, ast.FunctionDef):
            result["functions"].append({
                "name": node.name,
                "line": node.lineno
            })

        elif isinstance(node, ast.ClassDef):
            result["classes"].append({
                "name": node.name,
                "line": node.lineno
            })

        elif isinstance(node, ast.Import):

            for alias in node.names:
                result["imports"].append(alias.name)

        elif isinstance(node, ast.ImportFrom):

            module = node.module if node.module else ""

            for alias in node.names:
                result["imports"].append(
                    f"{module}.{alias.name}"
                )

    return result


def analyze_project(project_path):

    project = []

    for root, dirs, files in os.walk(project_path):

        dirs[:] = [
            d for d in dirs
            if d not in {
                ".venv",
                "__pycache__",
                ".git"
            }
        ]

        for file in files:

            if not file.endswith(".py"):
                continue

            path = os.path.join(root, file)

            data = analyze_python_file(path)

            if data:
                project.append(data)

    return project