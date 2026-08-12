from system_layer.project_indexer import search_code
import os
import re


skill = {
    "name": "Project Search",
    "priority": 45
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value):
    """
    Normalize text for project searching.
    """

    if not value:
        return ""

    value = str(value)

    # CamelCase
    value = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1 \2",
        value
    )

    value = value.lower()

    value = (
        value
        .replace("_", " ")
        .replace("-", " ")
    )

    return " ".join(
        value.split()
    )


# ============================================================
# COMMAND DETECTION
# ============================================================

def can_handle(command):

    command = normalize(
        command
    )

    keywords = [
        "where is",
        "find",
        "locate",
        "search for",
        "used",
        "where can i find",
        "show me where",
        "where can i see",
    ]

    return any(
        command.startswith(keyword)
        for keyword in keywords
    )


# ============================================================
# QUERY EXTRACTION
# ============================================================

def extract_query(command):

    command = command.lower().strip()

    prefixes = [
        "where can i find",
        "where can i see",
        "show me where",
        "search for",
        "where is",
        "locate",
        "find",
        "used",
    ]

    for prefix in prefixes:

        if command.startswith(prefix):

            query = command[
                len(prefix):
            ].strip()

            return query

    return command


# ============================================================
# IDENTIFIER HELPERS
# ============================================================

def identifier(value):
    """
    Convert:

        process command
        process-command
        process_command

    into:

        process_command
    """

    normalized = normalize(value)

    return "_".join(
        normalized.split()
    )


# ============================================================
# RESULT RANKING
# ============================================================

def rank_result(result, query):

    normalized_query = normalize(
        query
    )

    query_identifier = identifier(
        query
    )

    score = result.get(
        "score",
        0
    )

    match_type = result.get(
        "match"
    )

    result_type = result.get(
        "type"
    )

    result_name = result.get(
        "name"
    )

    file_path = result.get(
        "file",
        ""
    ).replace("\\", "/")

    filename = os.path.basename(
        file_path
    ).lower()

    filename_without_extension = os.path.splitext(
        filename
    )[0]

    normalized_filename = normalize(
        filename_without_extension
    )

    # ========================================================
    # STRUCTURAL MATCH BONUS
    # ========================================================

    if match_type == "definition":
        score += 250

    elif match_type == "identifier":
        score += 80

    elif match_type == "filename":
        score += 60

    elif match_type == "path":
        score += 30

    elif match_type == "reference":
        score += 0

    # ========================================================
    # EXACT FUNCTION / CLASS NAME
    # ========================================================

    if result_name:

        normalized_name = normalize(
            result_name
        )

        result_identifier = identifier(
            result_name
        )

        if result_identifier == query_identifier:

            score += 300

        elif normalized_name == normalized_query:

            score += 250

    # ========================================================
    # EXACT FILE NAME
    # ========================================================

    if normalized_filename == normalized_query:

        score += 200

    # ========================================================
    # QUERY IN FILE NAME
    # ========================================================

    elif normalized_query in normalized_filename:

        score += 80

    # ========================================================
    # SOURCE DIRECTORY
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

    first_directory = (
        file_path.split("/")[0]
        if "/" in file_path
        else file_path
    )

    if first_directory in source_dirs:

        score += 25

    # ========================================================
    # TEST PENALTY
    # ========================================================

    if (
        filename.startswith("test_")
        or filename.endswith("_test.py")
    ):

        score -= 200

    # ========================================================
    # DOCUMENTATION PENALTY
    # ========================================================

    if (
        filename.startswith("readme")
        or filename.endswith(".md")
        or filename.endswith(".txt")
    ):

        score -= 100

    # ========================================================
    # DEBUG
    # ========================================================

    print(
        f"[V5 PROJECT RANK] "
        f"{file_path} "
        f"| match={match_type} "
        f"| type={result_type} "
        f"| name={result_name} "
        f"| score={score}"
    )

    return score


# ============================================================
# RESPONSE HELPERS
# ============================================================

def format_result(result):

    file_path = result["file"]

    line = result["line"]

    result_type = result.get(
        "type"
    )

    result_name = result.get(
        "name"
    )

    if (
        result_type
        in ("function", "class")
        and result_name
    ):

        return (
            f"{file_path} "
            f"({result_type} "
            f"{result_name}, "
            f"line {line})"
        )

    return (
        f"{file_path} "
        f"(line {line})"
    )


# ============================================================
# PROJECT SEARCH
# ============================================================

def execute(command):

    command = command.lower().strip()

    # ========================================================
    # EXTRACT QUERY
    # ========================================================

    query = extract_query(
        command
    )

    if not query:

        return (
            "What would you like me "
            "to search for?"
        )

    # ========================================================
    # SEARCH PROJECT
    # ========================================================

    results = search_code(
        ".",
        query
    )

    if not results:

        return (
            f"I couldn't find "
            f"{query}."
        )

    # ========================================================
    # RANK RESULTS
    # ========================================================

    ranked_results = sorted(
        results,
        key=lambda result: rank_result(
            result,
            query
        ),
        reverse=True
    )

    # ========================================================
    # BEST RESULT
    # ========================================================

    best = ranked_results[0]

    best_file = best["file"]

    best_line = best["line"]

    best_type = best.get(
        "type"
    )

    best_name = best.get(
        "name"
    )

    spoken_query = (
        query
        .replace("_", " ")
        .replace("-", " ")
    )

    # ========================================================
    # EXACT STRUCTURAL RESULT
    # ========================================================

    if (
        best_type in (
            "function",
            "class",
        )
        and best_name
    ):

        if best_type == "function":

            opening = (
                f"Sir, I found the function "
                f"{best_name} in "
                f"{best_file}, at line "
                f"{best_line}."
            )

        else:

            opening = (
                f"Sir, I found the class "
                f"{best_name} in "
                f"{best_file}, at line "
                f"{best_line}."
            )

    else:

        opening = (
            f"Sir, the best match for "
            f"{spoken_query} is "
            f"{best_file}, at line "
            f"{best_line}."
        )

    # ========================================================
    # SINGLE RESULT
    # ========================================================

    if len(ranked_results) == 1:

        return opening

    # ========================================================
    # MULTIPLE RESULTS
    # ========================================================

    reply = (
        opening
        + "\n\n"
        + f"I found {len(ranked_results)} "
        f"relevant result(s) in total."
    )

    # ========================================================
    # OTHER RESULTS
    # ========================================================

    others = ranked_results[1:5]

    if others:

        reply += (
            "\n\nOther relevant locations:"
        )

        for result in others:

            reply += (
                "\n"
                + format_result(result)
            )

    # ========================================================
    # REMAINING
    # ========================================================

    remaining = (
        len(ranked_results) - 5
    )

    if remaining > 0:

        reply += (
            f"\n\nThere are "
            f"{remaining} more "
            f"result(s)."
        )

    return reply