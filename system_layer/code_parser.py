import ast
import os


def build_code_index(project_path="."):
    """
    Build an index of every Python file in the project.
    """

    index = {
        "functions": [],
        "classes": [],
        "imports": []
    }

    for root, _, files in os.walk(project_path):

        for file in files:

            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)

            try:

                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()

                tree = ast.parse(source)

            except Exception:
                continue

            relative = os.path.relpath(filepath, project_path)

            for node in ast.walk(tree):

                if isinstance(node, ast.FunctionDef):

                    index["functions"].append({
                        "name": node.name,
                        "file": relative,
                        "line": node.lineno,
                        "args": [
                            arg.arg
                            for arg in node.args.args
                        ]
                    })

                elif isinstance(node, ast.ClassDef):

                    index["classes"].append({
                        "name": node.name,
                        "file": relative,
                        "line": node.lineno
                    })

                elif isinstance(node, ast.Import):

                    for alias in node.names:

                        index["imports"].append({
                            "module": alias.name,
                            "file": relative
                        })

                elif isinstance(node, ast.ImportFrom):

                    module = node.module or ""

                    for alias in node.names:

                        index["imports"].append({
                            "module": module,
                            "name": alias.name,
                            "file": relative
                        })

    return index