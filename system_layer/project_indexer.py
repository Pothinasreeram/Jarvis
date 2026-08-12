import os
import re
import ast

# ============================================================
# PROJECT INDEXER V5
# ============================================================
#
# V5 improvements:
#
# - Exact function/class definition detection
# - Strong identifier matching
# - Better natural-language query handling
# - Structural match types
# - Definition > reference > incidental match
# - File/path relevance
# - Test/documentation penalties
# - Duplicate-location protection
# - Weak-result filtering
# - Keeps build_project_index() and search_code()
#
# ============================================================


# ============================================================
# CONFIGURATION
# ============================================================

IGNORE_DIRS = {
    ".venv",
    "__pycache__",
    ".git",
    "node_modules",
    "screenshots",
    "build",
    "dist",
    ".idea",
    ".vscode",
}

ALLOWED_EXTENSIONS = {
    ".py",
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
}

GENERIC_WORDS = {
    "the",
    "is",
    "where",
    "find",
    "locate",
    "search",
    "for",
    "can",
    "i",
    "me",
    "show",
    "please",
    "my",
    "in",
    "at",
    "on",
    "of",
    "to",
    "tell",
    "give",
    "get",
    "look",
    "lookfor",
    "code",
    "file",
    "files",
    "function",
    "method",
    "class",
}

MAX_RESULTS = 15

# Minimum score required for a result to survive.
MIN_RESULT_SCORE = 20


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize(text):
    """
    Normalize text for search.

    Examples:

        process_command
        process command
        process-command
        processCommand

    become:

        process command
    """

    if not text:
        return ""

    text = str(text)

    # IMPORTANT:
    # Split CamelCase BEFORE lowercasing.
    text = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1 \2",
        text,
    )

    text = re.sub(
        r"([A-Z]+)([A-Z][a-z])",
        r"\1 \2",
        text,
    )

    text = text.lower()

    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = text.replace(".", " ")

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    return " ".join(text.split())


# ============================================================
# IDENTIFIER NORMALIZATION
# ============================================================

def normalize_identifier(text):
    """
    Normalize an identifier.

    process_command
    processCommand
    process-command

    all become:

        process command
    """

    return normalize(text)


def identifier_form(text):
    """
    Convert normalized text into identifier form.

    Example:

        process command -> process_command
    """

    normalized = normalize(text)

    if not normalized:
        return ""

    return "_".join(normalized.split())


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text):
    """
    Extract meaningful search tokens.
    """

    normalized = normalize(text)

    if not normalized:
        return []

    return [
        word
        for word in normalized.split()
        if word not in GENERIC_WORDS
    ]


# ============================================================
# DIRECTORY FILTER
# ============================================================

def should_ignore_directory(directory):
    return directory in IGNORE_DIRS


# ============================================================
# FILE FILTER
# ============================================================

def is_allowed_file(filepath):
    extension = os.path.splitext(filepath)[1].lower()
    return extension in ALLOWED_EXTENSIONS


# ============================================================
# TEST FILE DETECTION
# ============================================================

def is_test_file(filepath):
    filename = os.path.basename(filepath).lower()

    return (
        filename.startswith("test_")
        or filename.endswith("_test.py")
        or filename.startswith("test.")
    )


# ============================================================
# DOCUMENTATION FILE DETECTION
# ============================================================

def is_documentation_file(filepath):
    filename = os.path.basename(filepath).lower()

    return (
        filename.startswith("readme")
        or filename.endswith(".md")
        or filename.endswith(".txt")
    )


# ============================================================
# COMMENT DETECTION
# ============================================================

def is_comment_line(line):
    stripped = line.strip()

    return (
        stripped.startswith("#")
        or stripped.startswith("//")
        or stripped.startswith("<!--")
    )


# ============================================================
# PYTHON STRUCTURE EXTRACTION
# ============================================================

def extract_python_definitions(lines):
    """
    Extract Python functions/classes using AST.

    Returns:

        {
            line_number: {
                "type": "function",
                "name": "process_command",
            }
        }
    """

    definitions = {}

    source = "".join(lines)

    try:
        tree = ast.parse(source)
    except Exception:
        return definitions

    for node in ast.walk(tree):

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):

            if isinstance(node, ast.ClassDef):
                definition_type = "class"
            else:
                definition_type = "function"

            definitions[node.lineno] = {
                "type": definition_type,
                "name": node.name,
            }

    return definitions


# ============================================================
# QUERY ANALYSIS
# ============================================================

def analyze_query(query):
    """
    Analyze a natural-language project-search query.
    """

    normalized = normalize(query)

    tokens = tokenize(query)

    return {
        "normalized": normalized,
        "tokens": tokens,
        "identifier": identifier_form(query),
    }


# ============================================================
# TOKEN MATCHING
# ============================================================

def token_match_score(text, query_tokens):
    if not query_tokens:
        return 0, 0.0

    normalized_text = normalize(text)

    matched = 0

    for token in query_tokens:
        if token in normalized_text:
            matched += 1

    ratio = matched / len(query_tokens)

    return matched, ratio


# ============================================================
# MATCH TYPE
# ============================================================

def determine_match_type(
    line,
    definition,
    normalized_query,
    query_tokens,
    relative_path,
):
    """
    Determine what kind of match produced the result.

    Priority:

        definition
        identifier
        filename
        path
        reference
        incidental
    """

    normalized_line = normalize(line)

    if definition:

        definition_name = normalize_identifier(
            definition["name"]
        )

        if definition_name == normalized_query:
            return "definition"

        definition_tokens = tokenize(
            definition["name"]
        )

        if (
            query_tokens
            and all(
                token in definition_tokens
                for token in query_tokens
            )
        ):
            return "definition"

    if normalized_query in normalized_line:
        return "identifier"

    normalized_filename = normalize(
        os.path.basename(relative_path)
    )

    if normalized_query in normalized_filename:
        return "filename"

    normalized_path = normalize(relative_path)

    if normalized_query in normalized_path:
        return "path"

    return "reference"


# ============================================================
# RELEVANCE SCORE V5
# ============================================================

def calculate_score(
    filepath,
    line,
    query,
    normalized_query,
    query_tokens,
    definition=None,
):
    """
    Calculate V5 relevance score.

    Exact definitions receive the strongest score.
    """

    score = 0

    relative_path = filepath.replace("\\", "/")

    filename = os.path.basename(relative_path)

    normalized_path = normalize(relative_path)

    normalized_filename = normalize(filename)

    normalized_line = normalize(line)

    stripped = line.strip()

    query_identifier = identifier_form(query)

    # ========================================================
    # 1. EXACT FUNCTION / CLASS DEFINITION
    # ========================================================

    if definition:

        definition_name = definition["name"]

        normalized_definition = normalize_identifier(
            definition_name
        )

        definition_identifier = identifier_form(
            definition_name
        )

        # EXACT identifier
        if definition_identifier == query_identifier:

            score += 500

        # Exact normalized name
        elif normalized_definition == normalized_query:

            score += 450

        # Query contained inside definition
        elif normalized_query in normalized_definition:

            score += 300

        # Token matching
        definition_tokens = tokenize(
            definition_name
        )

        matched = sum(
            1
            for token in query_tokens
            if token in definition_tokens
        )

        if matched:

            score += matched * 60

            if (
                query_tokens
                and matched == len(query_tokens)
            ):
                score += 100

        # Function/class structural bonus
        if definition["type"] == "function":
            score += 50

        elif definition["type"] == "class":
            score += 45

    # ========================================================
    # 2. EXACT LINE MATCH
    # ========================================================

    if normalized_line == normalized_query:
        score += 180

    # ========================================================
    # 3. QUERY IN LINE
    # ========================================================

    if (
        normalized_query
        and normalized_query in normalized_line
    ):
        score += 90

    # ========================================================
    # 4. QUERY IN FILENAME
    # ========================================================

    if (
        normalized_query
        and normalized_query in normalized_filename
    ):
        score += 160

    # ========================================================
    # 5. QUERY IN PATH
    # ========================================================

    if (
        normalized_query
        and normalized_query in normalized_path
    ):
        score += 100

    # ========================================================
    # 6. TOKEN MATCHING
    # ========================================================

    line_matches, line_ratio = token_match_score(
        normalized_line,
        query_tokens,
    )

    filename_matches, filename_ratio = token_match_score(
        normalized_filename,
        query_tokens,
    )

    path_matches, path_ratio = token_match_score(
        normalized_path,
        query_tokens,
    )

    score += line_matches * 15
    score += filename_matches * 30
    score += path_matches * 15

    # All query tokens on line
    if query_tokens and line_ratio == 1.0:
        score += 50

    # All query tokens in filename
    if query_tokens and filename_ratio == 1.0:
        score += 80

    # ========================================================
    # 7. SOURCE DIRECTORY BONUS
    # ========================================================

    source_dirs = {
        "ai_brain",
        "core",
        "system_layer",
        "command_system",
        "memory_layer",
        "skills",
        "gui",
        "voice_engine",
    }

    first_directory = relative_path.split("/")[0]

    if first_directory in source_dirs:
        score += 20

    # ========================================================
    # 8. IMPORT BONUS
    # ========================================================

    if stripped.startswith("from "):
        score += 10

    elif stripped.startswith("import "):
        score += 10

    # ========================================================
    # 9. TEST PENALTY
    # ========================================================

    if is_test_file(filepath):
        score -= 150

    # ========================================================
    # 10. DOCUMENTATION PENALTY
    # ========================================================

    if is_documentation_file(filepath):
        score -= 80

    # ========================================================
    # 11. COMMENT PENALTY
    # ========================================================

    if is_comment_line(line):
        score -= 60

    # ========================================================
    # 12. DOCSTRING PENALTY
    # ========================================================

    if (
        stripped.startswith('"""')
        or stripped.startswith("'''")
    ):
        score -= 30

    return score


# ============================================================
# SNIPPET BUILDER
# ============================================================

def build_snippet(
    lines,
    line_number,
    context=5,
):
    index = line_number - 1

    start = max(
        0,
        index - context,
    )

    end = min(
        len(lines),
        index + context + 1,
    )

    snippet = []

    for i in range(start, end):

        snippet.append(
            f"{i + 1:4} | "
            f"{lines[i].rstrip()}"
        )

    return "\n".join(snippet)


# ============================================================
# PROJECT INDEX
# ============================================================

def build_project_index(project_path="."):
    """
    Build a project-wide source index.
    """

    index = {}

    project_path = os.path.abspath(
        project_path
    )

    print("Building project index...")

    for root, dirs, files in os.walk(
        project_path
    ):

        dirs[:] = [
            directory
            for directory in dirs
            if not should_ignore_directory(directory)
        ]

        for file in files:

            if not is_allowed_file(file):
                continue

            full_path = os.path.join(
                root,
                file,
            )

            try:

                with open(
                    full_path,
                    "r",
                    encoding="utf-8",
                ) as f:

                    code = f.read()

                relative_path = os.path.relpath(
                    full_path,
                    project_path,
                )

                index[relative_path] = code

            except Exception as e:

                print(
                    f"Could not read {full_path}: {e}"
                )

    return index


# ============================================================
# CODE SEARCH V5
# ============================================================

def search_code(
    project_path,
    query,
    context=5,
):
    """
    Search project source files.

    Returns ranked structured results.
    """

    results = []

    query_info = analyze_query(query)

    normalized_query = query_info["normalized"]

    query_tokens = query_info["tokens"]

    if not normalized_query:
        return results

    if not query_tokens:
        return results

    project_path = os.path.abspath(
        project_path
    )

    # ========================================================
    # WALK PROJECT
    # ========================================================

    for root, dirs, files in os.walk(
        project_path
    ):

        dirs[:] = [
            directory
            for directory in dirs
            if not should_ignore_directory(directory)
        ]

        for file in files:

            if not is_allowed_file(file):
                continue

            filepath = os.path.join(
                root,
                file,
            )

            relative_path = os.path.relpath(
                filepath,
                project_path,
            )

            # =================================================
            # READ FILE
            # =================================================

            try:

                with open(
                    filepath,
                    "r",
                    encoding="utf-8",
                ) as f:

                    lines = f.readlines()

            except Exception as e:

                print(
                    f"Could not search {filepath}: {e}"
                )

                continue

            # =================================================
            # PYTHON DEFINITIONS
            # =================================================

            if filepath.lower().endswith(".py"):

                definitions = extract_python_definitions(
                    lines
                )

            else:

                definitions = {}

            normalized_path = normalize(
                relative_path
            )

            normalized_filename = normalize(
                file
            )

            # =================================================
            # SEARCH LINES
            # =================================================

            for i, line in enumerate(lines):

                normalized_line = normalize(line)

                if not normalized_line:
                    continue

                # ------------------------------------------------
                # MATCH DETECTION
                # ------------------------------------------------

                exact_match = (
                    normalized_query in normalized_line
                )

                token_matches = [
                    token
                    for token in query_tokens
                    if token in normalized_line
                ]

                path_match = (
                    normalized_query in normalized_path
                )

                filename_match = (
                    normalized_query in normalized_filename
                )

                definition = definitions.get(
                    i + 1
                )

                # ------------------------------------------------
                # DEFINITION NAME MATCH
                # ------------------------------------------------

                definition_match = False

                if definition:

                    definition_name = normalize_identifier(
                        definition["name"]
                    )

                    definition_tokens = tokenize(
                        definition["name"]
                    )

                    if (
                        definition_name == normalized_query
                        or normalized_query in definition_name
                        or (
                            query_tokens
                            and all(
                                token in definition_tokens
                                for token in query_tokens
                            )
                        )
                    ):
                        definition_match = True

                # ------------------------------------------------
                # IGNORE UNRELATED LINES
                # ------------------------------------------------

                if not (
                    exact_match
                    or token_matches
                    or path_match
                    or filename_match
                    or definition_match
                ):
                    continue

                # =================================================
                # MATCH TYPE
                # =================================================

                match_type = determine_match_type(
                    line,
                    definition if definition_match else None,
                    normalized_query,
                    query_tokens,
                    relative_path,
                )

                # =================================================
                # SCORE
                # =================================================

                score = calculate_score(
                    relative_path,
                    line,
                    query,
                    normalized_query,
                    query_tokens,
                    definition if definition_match else None,
                )

                # Additional multi-token bonus
                if len(token_matches) > 1:
                    score += len(token_matches) * 10

                # =================================================
                # WEAK RESULT FILTER
                # =================================================

                if score < MIN_RESULT_SCORE:
                    continue

                # =================================================
                # SNIPPET
                # =================================================

                snippet = build_snippet(
                    lines,
                    i + 1,
                    context,
                )

                # =================================================
                # RESULT
                # =================================================

                result = {
                    "file": relative_path,
                    "line": i + 1,
                    "snippet": snippet,
                    "score": score,
                    "match": match_type,
                }

                if definition_match:

                    result["type"] = definition["type"]

                    result["name"] = definition["name"]

                else:

                    result["type"] = "reference"

                    result["name"] = None

                results.append(result)

    # ========================================================
    # SORT
    # ========================================================

    results.sort(
        key=lambda result: (
            result["score"],
            1 if result["match"] == "definition" else 0,
            result["line"],
        ),
        reverse=True,
    )

    # ========================================================
    # REMOVE DUPLICATE LOCATIONS
    # ========================================================

    unique_results = []

    seen = set()

    for result in results:

        key = (
            result["file"],
            result["line"],
        )

        if key in seen:
            continue

        seen.add(key)

        unique_results.append(result)

    # ========================================================
    # DEBUG RANKING
    # ========================================================

    for result in unique_results[:MAX_RESULTS]:

        print(
            f"[V5 RANK] "
            f"{result['file']} "
            f"| line={result['line']} "
            f"| match={result['match']} "
            f"| type={result['type']} "
            f"| name={result['name']} "
            f"| score={result['score']}"
        )

    # ========================================================
    # RETURN TOP RESULTS
    # ========================================================

    return unique_results[:MAX_RESULTS]