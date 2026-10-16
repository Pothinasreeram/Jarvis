import os
import re
import ast
from collections import defaultdict


# ============================================================
# PROJECT INDEXER V6.6
# ============================================================
#
# V6.6 - RELATIONSHIP INTELLIGENCE CODE SEARCH
#
# Built on V6.5:
#
# - Exact definition detection
# - Exact identifier detection
# - Search intent detection
# - Function/class parent detection
# - Async detection
# - Import/reference/call classification
# - Documentation suppression
# - Comment suppression
# - Docstring suppression
# - Self-indexer suppression
# - Strong definition ranking
# - Exact-reference ranking
# - Filename/path relevance
# - Duplicate-location protection
# - Weak-result filtering
# - Natural-language query understanding
# - Operation detection
# - Startup/entry-point detection
# - Semantic concept extraction
# - Synonym expansion
# - Semantic identifier candidates
# - Intent-aware candidate ranking
# - Weighted semantic synonyms
# - Query subject/action/object extraction
# - Better conversational query parsing
# - Relationship-aware search
# - Caller/callee understanding
# - Function-level context
# - Class-level context
# - Semantic confidence scoring
# - Exact > structural > semantic ranking
# - Better startup detection
# - Better GUI detection
# - Better handler detection
# - Better semantic filename ranking
# - Stronger generic semantic suppression
# - Search target confidence
#
# NEW V6.6:
#
# - AST call graph
# - AST caller detection
# - AST callee detection
# - AST import graph
# - Function relationship extraction
# - Class relationship extraction
# - Method-aware relationships
# - Caller/callee relationship scoring
# - Real Python call detection
# - Attribute-call detection
# - Imported-name detection
# - Relationship-aware query parsing
# - Better "what does X call"
# - Better "who calls X"
# - Better "what uses X"
# - Better "where X is imported"
# - Better relationship filtering
# - Relationship confidence
# - Semantic confidence
# - Query target confidence
# - Improved startup detection
# - Improved GUI detection
# - Improved handler detection
# - Improved false-positive suppression
# - Improved result metadata
#
# Public API:
#
#     build_project_index()
#     search_code()
#
# Python:
#
#     3.11+
#
# ============================================================


# ============================================================
# CONFIGURATION
# ============================================================

IGNORE_DIRS = {
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".git",
    "node_modules",
    "screenshots",
    "build",
    "dist",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "coverage",
    "htmlcov",
}

ALLOWED_EXTENSIONS = {
    ".py",
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
}


# ============================================================
# GENERIC SEARCH WORDS
# ============================================================

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
    "a",
    "an",
    "that",
    "which",
    "what",
    "who",
    "does",
    "do",
    "did",
    "how",
    "would",
    "could",
    "should",
    "this",
    "it",
    "its",
    "there",
    "code",
    "file",
    "files",
    "function",
    "functions",
    "method",
    "methods",
    "class",
    "classes",
    "definition",
    "definitions",
    "reference",
    "references",
    "usage",
    "usages",
    "called",
    "call",
    "calls",
    "located",
    "location",
    "source",
    "implementation",
    "implemented",
    "declared",
    "project",
    "sourcecode",
    "sourcefiles",
    "command",
}


# ============================================================
# SEARCH OPERATOR WORDS
# ============================================================

SEARCH_OPERATOR_WORDS = {
    "where",
    "find",
    "locate",
    "show",
    "search",
    "look",
    "lookfor",
    "tell",
    "give",
    "get",
    "please",
    "can",
    "i",
    "me",
    "my",
    "what",
    "who",
    "does",
    "do",
    "did",
    "how",
    "could",
    "would",
    "should",
}


# ============================================================
# GENERIC CODE CONCEPT WORDS
# ============================================================

GENERIC_CODE_WORDS = {
    "code",
    "file",
    "files",
    "function",
    "functions",
    "method",
    "methods",
    "class",
    "classes",
    "definition",
    "definitions",
    "reference",
    "references",
    "usage",
    "usages",
    "source",
    "implementation",
    "project",
    "sourcecode",
    "sourcefiles",
    "command",
}


# ============================================================
# INTENT KEYWORDS
# ============================================================

LOCATION_KEYWORDS = {
    "where",
    "locate",
    "location",
    "located",
}

DEFINITION_KEYWORDS = {
    "definition",
    "defined",
    "function",
    "functions",
    "method",
    "methods",
    "class",
    "classes",
    "implementation",
    "implemented",
    "declared",
    "handles",
    "handle",
}

REFERENCE_KEYWORDS = {
    "reference",
    "references",
    "usage",
    "usages",
    "used",
    "called",
    "calls",
    "call",
    "uses",
    "use",
    "import",
    "imports",
}

IMPORT_KEYWORDS = {
    "import",
    "imports",
    "imported",
}

CALL_KEYWORDS = {
    "call",
    "calls",
    "called",
    "invokes",
    "invoke",
}

STARTUP_KEYWORDS = {
    "start",
    "starts",
    "startup",
    "entry",
    "entrypoint",
    "launch",
    "launcher",
    "main",
    "boot",
    "boots",
    "initialize",
    "initialization",
}

GUI_KEYWORDS = {
    "gui",
    "interface",
    "ui",
    "window",
    "windows",
    "screen",
    "widget",
    "widgets",
    "display",
}

HANDLER_KEYWORDS = {
    "handle",
    "handles",
    "handler",
    "process",
    "processes",
    "processing",
    "manage",
    "manages",
    "controller",
    "controls",
}


# ============================================================
# PHRASES
# ============================================================

USAGE_PHRASES = {
    "what calls",
    "who calls",
    "what uses",
    "who uses",
    "where used",
    "where is used",
    "where are references",
    "show references",
    "find references",
    "who invokes",
    "what invokes",
}

IMPORT_PHRASES = {
    "where imported",
    "where is imported",
    "where imports",
    "show imports",
    "find imports",
    "what imports",
}

DEFINITION_PHRASES = {
    "where is",
    "where are",
    "show",
    "show me",
    "find",
    "locate",
    "definition of",
    "implementation of",
    "function that",
    "function which",
    "class that",
    "class which",
}

STARTUP_PHRASES = {
    "where does",
    "where does it",
    "where does jarvis",
    "where jarvis starts",
    "where does jarvis start",
    "where does the application start",
    "where does the app start",
    "entry point",
    "starting point",
}

CALLER_PHRASES = {
    "what calls",
    "who calls",
    "what invokes",
    "who invokes",
    "where called",
    "where is called",
}

CALLEE_PHRASES = {
    "what does",
    "what does it call",
    "what does function call",
    "what does method call",
    "what does class call",
    "what does it invoke",
}


# ============================================================
# V6.6 RELATIONSHIP TYPES
# ============================================================

RELATIONSHIP_CALLER = "caller"
RELATIONSHIP_CALLEE = "callee"
RELATIONSHIP_IMPORTER = "importer"
RELATIONSHIP_IMPORTED = "imported"
RELATIONSHIP_TARGET = "target"
RELATIONSHIP_HANDLER = "handler"
RELATIONSHIP_STARTUP = "startup"


# ============================================================
# V6.5 / V6.6 WEIGHTED SEMANTIC SYNONYMS
# ============================================================

SEMANTIC_SYNONYMS = {

    "microphone": {
        "microphone": 1.00,
        "mic": 0.95,
        "pyaudio": 0.88,
        "recorder": 0.82,
        "record": 0.78,
        "listen": 0.72,
        "listener": 0.70,
        "speech": 0.55,
        "audio": 0.40,
        "input": 0.60,
    },

    "voice": {
        "voice": 1.00,
        "speech": 0.90,
        "speak": 0.88,
        "speaker": 0.82,
        "tts": 0.90,
        "stt": 0.90,
        "audio": 0.45,
        "pyttsx3": 0.88,
        "speechrecognition": 0.88,
        "recognizer": 0.88,
        "recognition": 0.82,
    },

    "volume": {
        "volume": 1.00,
        "sound": 0.75,
        "audio": 0.50,
        "mute": 0.90,
        "unmute": 0.90,
        "speaker": 0.70,
        "master": 0.55,
        "mixer": 0.72,
    },

    "gui": {
        "gui": 1.00,
        "ui": 0.95,
        "interface": 0.95,
        "window": 0.88,
        "screen": 0.78,
        "widget": 0.80,
        "customtkinter": 0.92,
        "tkinter": 0.88,
        "display": 0.70,
        "panel": 0.72,
        "canvas": 0.60,
    },

    "interface": {
        "interface": 1.00,
        "gui": 0.95,
        "ui": 0.95,
        "window": 0.88,
        "screen": 0.78,
        "widget": 0.80,
        "customtkinter": 0.92,
        "tkinter": 0.88,
    },

    "database": {
        "database": 1.00,
        "db": 0.90,
        "sqlite": 0.92,
        "mysql": 0.92,
        "postgres": 0.92,
        "query": 0.65,
        "connection": 0.70,
        "cursor": 0.65,
        "table": 0.60,
    },

    "internet": {
        "internet": 1.00,
        "web": 0.85,
        "online": 0.78,
        "http": 0.80,
        "https": 0.80,
        "request": 0.75,
        "requests": 0.78,
        "browser": 0.72,
        "search": 0.60,
        "url": 0.65,
    },

    "browser": {
        "browser": 1.00,
        "webbrowser": 0.95,
        "chrome": 0.90,
        "firefox": 0.90,
        "url": 0.80,
        "website": 0.82,
        "web": 0.65,
    },

    "memory": {
        "memory": 1.00,
        "remember": 0.95,
        "storage": 0.82,
        "context": 0.65,
        "history": 0.72,
        "recall": 0.85,
        "save": 0.62,
        "load": 0.62,
    },

    "music": {
        "music": 1.00,
        "song": 0.95,
        "songs": 0.95,
        "spotify": 0.90,
        "player": 0.88,
        "playlist": 0.90,
        "audio": 0.40,
        "track": 0.88,
    },

    "command": {
        "command": 1.00,
        "commands": 1.00,
        "process": 0.78,
        "processing": 0.78,
        "handler": 0.85,
        "router": 0.82,
        "intent": 0.70,
        "dispatch": 0.85,
        "execute": 0.78,
        "executor": 0.78,
    },

    "startup": {
        "startup": 1.00,
        "start": 0.95,
        "entry": 0.92,
        "main": 0.90,
        "launch": 0.92,
        "launcher": 0.90,
        "boot": 0.88,
        "initialize": 0.88,
        "initialization": 0.88,
        "run": 0.70,
    },

    "jarvis": {
        "jarvis": 1.00,
        "assistant": 0.90,
        "core": 0.75,
        "main": 0.85,
        "ai": 0.60,
    },

    "handler": {
        "handler": 1.00,
        "handle": 0.95,
        "process": 0.78,
        "controller": 0.85,
        "manage": 0.75,
        "dispatch": 0.82,
        "route": 0.72,
    },

    "assistant": {
        "assistant": 1.00,
        "jarvis": 0.92,
        "ai": 0.78,
        "agent": 0.80,
        "core": 0.60,
    },
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(text):
    """
    Normalize arbitrary text.

    Example:

        process_command
            ->
        process command

        processCommand
            ->
        process command
    """

    if text is None:
        return ""

    text = str(text)

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
    return normalize(text)


def identifier_form(text):
    normalized = normalize(text)

    if not normalized:
        return ""

    return "_".join(
        normalized.split()
    )


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text):
    normalized = normalize(text)

    if not normalized:
        return []

    return [
        word
        for word in normalized.split()
        if word not in GENERIC_WORDS
    ]


# ============================================================
# QUERY NOISE REMOVAL
# ============================================================

def remove_query_noise(query):
    normalized = normalize(query)

    if not normalized:
        return ""

    words = normalized.split()
    meaningful = []

    for word in words:

        if word in SEARCH_OPERATOR_WORDS:
            continue

        if word in {
            "the",
            "a",
            "an",
            "that",
            "which",
            "does",
            "do",
            "did",
            "it",
            "this",
            "my",
            "me",
            "please",
            "code",
            "file",
            "files",
            "source",
        }:
            continue

        meaningful.append(word)

    return " ".join(
        meaningful
    )


# ============================================================
# OPERATION DETECTION
# ============================================================

def detect_search_operation(query):
    """
    Returns:

        definition
        reference
        call
        import
        startup
        semantic
        general
    """

    normalized = normalize(query)
    words = set(normalized.split())

    # --------------------------------------------------------
    # Import
    # --------------------------------------------------------

    for phrase in IMPORT_PHRASES:

        if phrase in normalized:
            return "import"

    if words.intersection(
        IMPORT_KEYWORDS
    ):
        return "import"

    # --------------------------------------------------------
    # Caller / reference
    # --------------------------------------------------------

    for phrase in CALLER_PHRASES:

        if phrase in normalized:
            return "reference"

    for phrase in USAGE_PHRASES:

        if phrase in normalized:
            return "reference"

    # --------------------------------------------------------
    # Explicit call
    # --------------------------------------------------------

    if words.intersection(
        CALL_KEYWORDS
    ):

        if (
            "what does" in normalized
            and "call" in normalized
        ):
            return "call"

        if (
            "where is" in normalized
            and "called" in normalized
        ):
            return "reference"

        return "call"

    # --------------------------------------------------------
    # Startup
    # --------------------------------------------------------

    for phrase in STARTUP_PHRASES:

        if phrase in normalized:
            return "startup"

    if words.intersection(
        STARTUP_KEYWORDS
    ):
        return "startup"

    # --------------------------------------------------------
    # Definition
    # --------------------------------------------------------

    for phrase in DEFINITION_PHRASES:

        if phrase in normalized:
            return "definition"

    if words.intersection(
        DEFINITION_KEYWORDS
    ):
        return "definition"

    return "general"


# ============================================================
# QUERY INTENT
# ============================================================

def detect_search_intent(query):

    normalized = normalize(query)

    words = set(
        normalized.split()
    )

    operation = detect_search_operation(
        query
    )

    if operation == "import":
        return "reference"

    if operation in {
        "reference",
        "call",
    }:
        return "reference"

    if operation == "startup":
        return "location"

    if words.intersection(
        DEFINITION_KEYWORDS
    ):
        return "definition"

    if words.intersection(
        REFERENCE_KEYWORDS
    ):
        return "reference"

    if words.intersection(
        LOCATION_KEYWORDS
    ):
        return "location"

    return "general"


# ============================================================
# QUERY SUBJECT / ACTION / OBJECT
# ============================================================

def extract_query_roles(query):

    normalized = normalize(query)
    words = normalized.split()

    operation = detect_search_operation(
        query
    )

    subject_tokens = []
    action_tokens = []
    object_tokens = []

    action_words = (
        CALL_KEYWORDS
        | HANDLER_KEYWORDS
        | STARTUP_KEYWORDS
        | {
            "use",
            "uses",
            "used",
            "import",
            "imports",
            "create",
            "creates",
            "created",
            "process",
            "processes",
            "control",
            "controls",
            "play",
            "plays",
            "open",
            "opens",
            "invoke",
            "invokes",
            "execute",
            "executes",
            "run",
            "runs",
        }
    )

    ignored = (
        SEARCH_OPERATOR_WORDS
        | GENERIC_CODE_WORDS
        | {
            "the",
            "a",
            "an",
            "that",
            "which",
            "does",
            "do",
            "did",
            "it",
            "this",
            "there",
            "really",
            "actually",
            "me",
            "please",
            "is",
            "are",
        }
    )

    meaningful = []

    for word in words:

        if word in ignored:
            continue

        if word in action_words:

            action_tokens.append(
                word
            )

            continue

        meaningful.append(
            word
        )

    if meaningful:
        subject_tokens = meaningful

    relation = RELATIONSHIP_TARGET

    if operation == "reference":
        relation = RELATIONSHIP_CALLER

    elif operation == "call":
        relation = RELATIONSHIP_CALLEE

    elif operation == "import":
        relation = RELATIONSHIP_IMPORTER

    elif operation == "startup":
        relation = RELATIONSHIP_STARTUP

    elif action_tokens:
        relation = "action"

    if (
        set(words).intersection(GUI_KEYWORDS)
        and not subject_tokens
    ):
        subject_tokens = [
            "gui"
        ]

    if (
        set(words).intersection(HANDLER_KEYWORDS)
        and subject_tokens
    ):
        relation = RELATIONSHIP_HANDLER

    return {
        "subject": subject_tokens,
        "action": action_tokens,
        "object": object_tokens,
        "relation": relation,
    }


# ============================================================
# TARGET TOKENIZATION
# ============================================================

def extract_target_tokens(query):

    original = str(query or "").strip()

    if not original:
        return []

    operation = detect_search_operation(original)

    # ============================================================
    # STEP 1 — Extract explicit code identifiers BEFORE normalize()
    # ============================================================

    identifiers = re.findall(
        r"\b[A-Za-z_][A-Za-z0-9_]*\b",
        original,
    )

    relationship_words = {
        "what",
        "does",
        "do",
        "who",
        "calls",
        "call",
        "called",
        "calling",
        "uses",
        "used",
        "using",
        "invokes",
        "invoke",
        "where",
        "is",
        "are",
        "import",
        "imports",
        "imported",
        "from",
        "the",
        "a",
        "an",
    }

    # Prefer identifiers containing "_" because they are
    # overwhelmingly likely to be actual code identifiers.
    for identifier in identifiers:

        lowered = identifier.lower()

        if lowered in relationship_words:
            continue

        if "_" in identifier:
            return [
                part
                for part in lowered.split("_")
                if part
            ]

    # ============================================================
    # STEP 2 — Handle ordinary identifiers
    # ============================================================

    candidates = []

    for identifier in identifiers:

        lowered = identifier.lower()

        if lowered in relationship_words:
            continue

        if lowered in SEARCH_OPERATOR_WORDS:
            continue

        if lowered in GENERIC_CODE_WORDS:
            continue

        candidates.append(lowered)

    # For natural-language queries, keep the actual target words.
    if candidates:
        return candidates

    # ============================================================
    # STEP 3 — Existing normalized fallback
    # ============================================================

    normalized = normalize(original)

    if not normalized:
        return []

    words = normalized.split()

    meaningful = []

    for word in words:

        if word in SEARCH_OPERATOR_WORDS:
            continue

        if word in GENERIC_CODE_WORDS:
            continue

        if word in {
            "what",
            "does",
            "do",
            "who",
            "calls",
            "call",
            "called",
            "calling",
            "uses",
            "used",
            "using",
            "invokes",
            "invoke",
            "where",
            "is",
            "are",
            "import",
            "imports",
            "imported",
            "from",
            "the",
            "a",
            "an",
        }:
            continue

        meaningful.append(word)

    return meaningful
# ============================================================
# SEMANTIC CONCEPT EXTRACTION
# ============================================================

def extract_semantic_concepts(query):

    normalized = normalize(query)

    words = set(
        normalized.split()
    )

    concepts = []

    for concept, synonyms in (
        SEMANTIC_SYNONYMS.items()
    ):

        if (
            concept in words
            or words.intersection(
                synonyms.keys()
            )
        ):

            concepts.append(
                concept
            )

    for word in extract_target_tokens(
        query
    ):

        if word not in concepts:
            concepts.append(
                word
            )

    unique = []
    seen = set()

    for item in concepts:

        if item in seen:
            continue

        seen.add(
            item
        )

        unique.append(
            item
        )

    return unique


# ============================================================
# SEMANTIC WEIGHT
# ============================================================

def semantic_weight(
    query_concept,
    line_word,
):

    query_concept = normalize(
        query_concept
    )

    line_word = normalize(
        line_word
    )

    if not query_concept or not line_word:
        return 0.0

    if query_concept == line_word:
        return 1.0

    synonyms = SEMANTIC_SYNONYMS.get(
        query_concept,
        {},
    )

    return synonyms.get(
        line_word,
        0.0,
    )


# ============================================================
# SEMANTIC LINE SCORE
# ============================================================

def semantic_line_score(
    line,
    query_info,
):

    concepts = query_info.get(
        "semantic_concepts",
        [],
    )

    if not concepts:
        return 0

    normalized_line = normalize(
        line
    )

    line_words = set(
        normalized_line.split()
    )

    score = 0

    for concept in concepts:

        if concept in line_words:

            score += 100
            continue

        synonyms = SEMANTIC_SYNONYMS.get(
            concept,
            {},
        )

        best_weight = 0.0

        for word in line_words:

            weight = synonyms.get(
                word,
                0.0,
            )

            best_weight = max(
                best_weight,
                weight,
            )

        if best_weight >= 0.90:
            score += 80

        elif best_weight >= 0.75:
            score += 60

        elif best_weight >= 0.50:
            score += 35

        elif best_weight >= 0.30:
            score += 15

    return score


# ============================================================
# V6.6 SEMANTIC CONFIDENCE
# ============================================================

def semantic_confidence(
    line,
    query_info,
):

    concepts = query_info.get(
        "semantic_concepts",
        [],
    )

    if not concepts:
        return 0.0

    normalized_line = normalize(
        line
    )

    line_words = set(
        normalized_line.split()
    )

    best = 0.0

    for concept in concepts:

        if concept in line_words:
            best = max(
                best,
                1.0,
            )
            continue

        synonyms = SEMANTIC_SYNONYMS.get(
            concept,
            {},
        )

        for word in line_words:

            weight = synonyms.get(
                word,
                0.0,
            )

            best = max(
                best,
                weight,
            )

    return round(
        best,
        3,
    )


# ============================================================
# IDENTIFIER CANDIDATES
# ============================================================

def generate_identifier_candidates(query):

    normalized = normalize(query)

    if not normalized:
        return []

    candidates = []

    target_tokens = extract_target_tokens(
        query
    )

    if target_tokens:

        target_identifier = "_".join(
            target_tokens
        )

        candidates.append(
            target_identifier
        )

    for token in target_tokens:

        if token not in candidates:

            candidates.append(
                token
            )

    original_query = str(query)

    explicit_identifiers = re.findall(
        r"\b[A-Za-z_][A-Za-z0-9_]*\b",
        original_query,
    )

    for identifier in explicit_identifiers:

        normalized_identifier = (
            identifier.lower()
        )

        if normalized_identifier in (
            SEARCH_OPERATOR_WORDS
            | GENERIC_WORDS
        ):
            continue

        if (
            "_" in identifier
            or (
                any(
                    char.isupper()
                    for char in identifier
                )
                and len(identifier) > 2
            )
        ):

            if identifier not in candidates:

                candidates.insert(
                    0,
                    identifier,
                )

    semantic_concepts = (
        extract_semantic_concepts(
            query
        )
    )

    for concept in semantic_concepts:

        identifier = identifier_form(
            concept
        )

        if (
            identifier
            and identifier not in candidates
        ):

            candidates.append(
                identifier
            )

    normalized_words = set(
        normalized.split()
    )

    if (
        "process" in normalized_words
        and "command" in normalized_words
    ):

        for candidate in [
            "process_command",
            "command_processor",
            "command_handler",
            "handle_command",
        ]:

            if candidate not in candidates:

                candidates.append(
                    candidate
                )

    if (
        "handle" in normalized_words
        and target_tokens
    ):

        for token in target_tokens:

            candidate = (
                f"handle_{token}"
            )

            if candidate not in candidates:

                candidates.append(
                    candidate
                )

    return candidates


# ============================================================
# QUERY ANALYSIS
# ============================================================

def analyze_query(query):

    normalized = normalize(
        query
    )

    operation = detect_search_operation(
        query
    )

    intent = detect_search_intent(
        query
    )

    target_tokens = extract_target_tokens(
        query
    )

    semantic_concepts = (
        extract_semantic_concepts(
            query
        )
    )

    candidates = (
        generate_identifier_candidates(
            query
        )
    )

    roles = extract_query_roles(
        query
    )

    if target_tokens:

        target = "_".join(
            target_tokens
        )

    elif candidates:

        target = candidates[0]

    else:

        target = ""

    return {
        "original": query,
        "normalized": normalized,
        "tokens": tokenize(query),
        "target_tokens": target_tokens,
        "semantic_concepts": semantic_concepts,
        "candidates": candidates,
        "target": target,
        "identifier": identifier_form(
            " ".join(
                target_tokens
            )
        )
        if target_tokens
        else "",
        "intent": intent,
        "operation": operation,
        "roles": roles,
        "relation": roles.get(
            "relation",
            RELATIONSHIP_TARGET,
        ),
    }


# ============================================================
# DIRECTORY FILTER
# ============================================================

def should_ignore_directory(directory):

    return directory.lower() in {
        item.lower()
        for item in IGNORE_DIRS
    }


# ============================================================
# FILE FILTER
# ============================================================

def is_allowed_file(filepath):

    extension = os.path.splitext(
        filepath
    )[1].lower()

    return extension in (
        ALLOWED_EXTENSIONS
    )


# ============================================================
# TEST FILE
# ============================================================

def is_test_file(filepath):

    filename = os.path.basename(
        filepath
    ).lower()

    return (
        filename.startswith("test_")
        or filename.endswith("_test.py")
        or filename.startswith("test.")
        or filename.endswith(".test.py")
    )


# ============================================================
# DOCUMENTATION FILE
# ============================================================

def is_documentation_file(filepath):

    filename = os.path.basename(
        filepath
    ).lower()

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
# DOCSTRING DETECTION
# ============================================================

def is_docstring_line(line):

    stripped = line.strip()

    return (
        stripped.startswith('"""')
        or stripped.startswith("'''")
    )


# ============================================================
# AST STRUCTURE
# ============================================================

def extract_python_structure(lines):

    structure = {}

    source = "".join(
        lines
    )

    try:

        tree = ast.parse(
            source
        )

    except Exception:

        return structure

    def visit(
        node,
        parent=None,
    ):

        if isinstance(
            node,
            ast.ClassDef,
        ):

            structure[node.lineno] = {
                "type": "class",
                "name": node.name,
                "parent": parent,
                "async": False,
            }

            for child in node.body:

                visit(
                    child,
                    node.name,
                )

            return

        if isinstance(
            node,
            ast.FunctionDef,
        ):

            structure[node.lineno] = {
                "type": "function",
                "name": node.name,
                "parent": parent,
                "async": False,
            }

            for child in node.body:

                visit(
                    child,
                    node.name,
                )

            return

        if isinstance(
            node,
            ast.AsyncFunctionDef,
        ):

            structure[node.lineno] = {
                "type": "function",
                "name": node.name,
                "parent": parent,
                "async": True,
            }

            for child in node.body:

                visit(
                    child,
                    node.name,
                )

            return

        for child in ast.iter_child_nodes(
            node
        ):

            visit(
                child,
                parent,
            )

    visit(
        tree,
        None,
    )

    return structure


# ============================================================
# BACKWARD-COMPATIBLE AST FUNCTION
# ============================================================

def extract_python_definitions(lines):

    return extract_python_structure(
        lines
    )


# ============================================================
# AST IDENTIFIER COLLECTION
# ============================================================

def extract_python_identifiers(lines):

    identifiers = set()

    source = "".join(
        lines
    )

    try:

        tree = ast.parse(
            source
        )

    except Exception:

        return identifiers

    for node in ast.walk(
        tree
    ):

        if isinstance(
            node,
            ast.Name,
        ):

            identifiers.add(
                node.id
            )

        elif isinstance(
            node,
            ast.Attribute,
        ):

            identifiers.add(
                node.attr
            )

        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):

            identifiers.add(
                node.name
            )

    return identifiers


# ============================================================
# V6.6 AST RELATIONSHIP EXTRACTION
# ============================================================

def get_called_name(node):

    if isinstance(
        node,
        ast.Name,
    ):
        return node.id

    if isinstance(
        node,
        ast.Attribute,
    ):

        parts = []

        current = node

        while isinstance(
            current,
            ast.Attribute,
        ):

            parts.append(
                current.attr
            )

            current = current.value

        if isinstance(
            current,
            ast.Name,
        ):

            parts.append(
                current.id
            )

        parts.reverse()

        return ".".join(
            parts
        )

    return None


def extract_python_relationships(lines):

    source = "".join(
        lines
    )

    relationships = {
        "functions": {},
        "classes": {},
        "calls": [],
        "imports": [],
        "imports_by_name": defaultdict(list),
        "callers_by_target": defaultdict(list),
        "callees_by_function": defaultdict(list),
    }

    try:

        tree = ast.parse(
            source
        )

    except Exception:

        return relationships

    function_stack = []
    class_stack = []

    def current_function():

        if not function_stack:
            return None

        return function_stack[-1]

    def current_class():

        if not class_stack:
            return None

        return class_stack[-1]

    def add_function(
        node,
        async_flag=False,
    ):

        parent = (
            current_class()
            or current_function()
        )

        info = {
            "type": "function",
            "name": node.name,
            "line": node.lineno,
            "end_line": getattr(
                node,
                "end_lineno",
                node.lineno,
            ),
            "parent": parent,
            "async": async_flag,
        }

        relationships[
            "functions"
        ][node.lineno] = info

        function_stack.append(
            node.name
        )

        for child in node.body:

            visit(
                child
            )

        function_stack.pop()

    def add_class(node):

        info = {
            "type": "class",
            "name": node.name,
            "line": node.lineno,
            "end_line": getattr(
                node,
                "end_lineno",
                node.lineno,
            ),
            "parent": current_class(),
        }

        relationships[
            "classes"
        ][node.lineno] = info

        class_stack.append(
            node.name
        )

        for child in node.body:

            visit(
                child
            )

        class_stack.pop()

    def visit(node):

        if isinstance(
            node,
            ast.ClassDef,
        ):

            add_class(
                node
            )

            return

        if isinstance(
            node,
            ast.FunctionDef,
        ):

            add_function(
                node,
                False,
            )

            return

        if isinstance(
            node,
            ast.AsyncFunctionDef,
        ):

            add_function(
                node,
                True,
            )

            return

        if isinstance(
            node,
            ast.Call,
        ):

            called_name = get_called_name(
                node.func
            )

            if called_name:

                caller = current_function()

                relationship = {
                    "type": "call",
                    "caller": caller,
                    "caller_class": current_class(),
                    "callee": called_name,
                    "line": node.lineno,
                    "end_line": getattr(
                        node,
                        "end_lineno",
                        node.lineno,
                    ),
                    "column": getattr(
                        node,
                        "col_offset",
                        0,
                    ),
                }

                relationships[
                    "calls"
                ].append(
                    relationship
                )

                if caller:

                    relationships[
                        "callees_by_function"
                    ][caller].append(
                        relationship
                    )

                    relationships[
                        "callers_by_target"
                    ][called_name].append(
                        relationship
                    )

        if isinstance(
            node,
            ast.Import,
        ):

            for alias in node.names:

                imported_name = (
                    alias.name
                )

                local_name = (
                    alias.asname
                    or imported_name.split(
                        "."
                    )[-1]
                )

                relationship = {
                    "type": "import",
                    "module": imported_name,
                    "name": local_name,
                    "alias": alias.asname,
                    "line": node.lineno,
                    "column": getattr(
                        node,
                        "col_offset",
                        0,
                    ),
                }

                relationships[
                    "imports"
                ].append(
                    relationship
                )

                relationships[
                    "imports_by_name"
                ][local_name].append(
                    relationship
                )

                relationships[
                    "imports_by_name"
                ][imported_name].append(
                    relationship
                )

        if isinstance(
            node,
            ast.ImportFrom,
        ):

            module = (
                node.module
                or ""
            )

            for alias in node.names:

                imported_name = (
                    alias.name
                )

                local_name = (
                    alias.asname
                    or imported_name
                )

                full_name = (
                    f"{module}.{imported_name}"
                    if module
                    else imported_name
                )

                relationship = {
                    "type": "import",
                    "module": module,
                    "name": local_name,
                    "imported": imported_name,
                    "full_name": full_name,
                    "alias": alias.asname,
                    "line": node.lineno,
                    "column": getattr(
                        node,
                        "col_offset",
                        0,
                    ),
                }

                relationships[
                    "imports"
                ].append(
                    relationship
                )

                relationships[
                    "imports_by_name"
                ][local_name].append(
                    relationship
                )

                relationships[
                    "imports_by_name"
                ][imported_name].append(
                    relationship
                )

                relationships[
                    "imports_by_name"
                ][full_name].append(
                    relationship
                )

        for child in ast.iter_child_nodes(
            node
        ):

            visit(
                child
            )

    visit(
        tree
    )

    return relationships


# ============================================================
# RELATIONSHIP INDEX
# ============================================================

def build_relationship_index(
    project_path,
):

    relationship_index = {
        "files": {},
        "callers": defaultdict(list),
        "callees": defaultdict(list),
        "imports": defaultdict(list),
        "definitions":defaultdict(list),
    }

    project_path = os.path.abspath(
        project_path
    )

    for root, dirs, files in os.walk(
        project_path
    ):

        dirs[:] = [
            directory
            for directory in dirs
            if not should_ignore_directory(
                directory
            )
        ]

        for file in files:

            if not is_allowed_file(
                file
            ):
                continue

            if not file.lower().endswith(
                ".py"
            ):
                continue

            filepath = os.path.join(
                root,
                file,
            )

            relative_path = os.path.relpath(
                filepath,
                project_path,
            )

            try:

                with open(
                    filepath,
                    "r",
                    encoding="utf-8",
                ) as f:

                    lines = f.readlines()

            except Exception:

                continue

            relationships = (
                extract_python_relationships(
                    lines
                )
            )

            relationship_index[
                "files"
            ][relative_path] = relationships

            for line, definition in (
                relationships[
                    "functions"
                ].items()
            ):

                name = definition[
                    "name"
                ]

                relationship_index[
                    "definitions"
                ].setdefault(
                    name,
                    []
                ).append(
                    {
                        "file": relative_path,
                        "line": line,
                        "definition": definition,
                    }
                )

            for call in relationships[
                "calls"
            ]:

                callee = call[
                    "callee"
                ]

                caller = call.get(
                    "caller"
                )

                callee_normalized = normalize_identifier(
                    callee
                )
                if callee_normalized:
                    relationship_index[
                        "callers"
                ].setdefault(
                    callee_normalized,
                    []
                ).append(
                    {
                        "file": relative_path,
                        "line": call[
                            "line"
                        ],
                        "relationship": call,
                    }
                )

                if caller:
                    
                    caller_key = normalize_identifier(
                        caller
                    )
                    if caller_key:
                        relationship_index[
                            "callees"
                    ].setdefault(
                        caller_key,
                        []
                    ).append(
                        {
                            "file": relative_path,
                            "line": call[
                                "line"
                            ],
                            "relationship": call,
                        }
                    )

            for import_info in relationships[
                "imports"
            ]:

                for key in {
                    import_info.get(
                        "name"
                    ),
                    import_info.get(
                        "module"
                    ),
                    import_info.get(
                        "imported"
                    ),
                    import_info.get(
                        "full_name"
                    ),
                }:

                    if not key:
                        continue

                    relationship_index[
                        "imports"
                    ][
                        normalize_identifier(
                            key
                        )
                    ].append(
                        {
                            "file": relative_path,
                            "line": import_info[
                                "line"
                            ],
                            "relationship": import_info,
                        }
                    )

    return relationship_index


# ============================================================
# EXACT IDENTIFIER MATCH
# ============================================================

def contains_exact_identifier(
    line,
    identifier,
):

    if not identifier:
        return False

    pattern = (
        r"(?<![A-Za-z0-9_])"
        + re.escape(identifier)
        + r"(?![A-Za-z0-9_])"
    )

    return re.search(
        pattern,
        line,
    ) is not None


# ============================================================
# LINE IDENTIFIERS
# ============================================================

def extract_line_identifiers(line):

    return set(
        re.findall(
            r"\b[A-Za-z_][A-Za-z0-9_]*\b",
            line,
        )
    )


# ============================================================
# IMPORT DETECTION
# ============================================================

def detect_import_type(line):

    stripped = line.strip()

    if stripped.startswith(
        "from "
    ):
        return "import"

    if stripped.startswith(
        "import "
    ):
        return "import"

    return None


# ============================================================
# FUNCTION CALL DETECTION
# ============================================================

def is_function_call(
    line,
    identifier,
):

    if not identifier:
        return False

    pattern = (
        r"(?<![A-Za-z0-9_])"
        + re.escape(identifier)
        + r"\s*\("
    )

    return re.search(
        pattern,
        line,
    ) is not None


# ============================================================
# SOURCE CODE LINE
# ============================================================

def looks_like_source_code(line):

    stripped = line.strip()

    if not stripped:
        return False

    if is_comment_line(
        line
    ):
        return False

    if is_docstring_line(
        line
    ):
        return False

    return True


# ============================================================
# SEMANTIC LINE MATCH
# ============================================================

def semantic_line_match(
    line,
    query_info,
):

    return (
        semantic_line_score(
            line,
            query_info,
        )
        > 0
    )


# ============================================================
# TARGET MATCH DEFINITION
# ============================================================

def target_matches_definition(
    definition,
    query_info,
):

    if not definition:
        return False

    name = definition[
        "name"
    ]

    normalized_name = normalize_identifier(
        name
    )

    definition_identifier = identifier_form(
        name
    )

    candidates = query_info[
        "candidates"
    ]

    target = query_info[
        "target"
    ]

    target_tokens = query_info[
        "target_tokens"
    ]

    semantic_concepts = query_info.get(
        "semantic_concepts",
        [],
    )

    if (
        definition_identifier
        in candidates
    ):
        return True

    if normalized_name == target:
        return True

    for candidate in candidates:

        if normalize_identifier(
            candidate
        ) == normalized_name:

            return True

    if (
        target
        and target in normalized_name
    ):
        return True

    definition_tokens = set(
        tokenize(name)
    )

    if (
        target_tokens
        and all(
            token in definition_tokens
            for token in target_tokens
        )
    ):
        return True

    for concept in semantic_concepts:

        normalized_concept = normalize(
            concept
        )

        if (
            normalized_concept
            and normalized_concept
            in normalized_name
        ):

            return True

    return False


# ============================================================
# TARGET MATCH SOURCE LINE
# ============================================================

def target_matches_line(
    line,
    query_info,
):

    candidates = query_info[
        "candidates"
    ]

    target = query_info[
        "target"
    ]

    for candidate in candidates:

        if contains_exact_identifier(
            line,
            candidate,
        ):
            return True

    normalized_line = normalize(
        line
    )

    if (
        target
        and target in normalized_line
    ):
        return True

    return False


# ============================================================
# MATCH TYPE
# ============================================================

def determine_match_type(
    line,
    definition,
    query_info,
    relative_path,
):

    if definition:

        if target_matches_definition(
            definition,
            query_info,
        ):

            return "definition"

    candidates = query_info[
        "candidates"
    ]

    for candidate in candidates:

        if contains_exact_identifier(
            line,
            candidate,
        ):

            import_type = detect_import_type(
                line
            )

            if import_type:
                return "import"

            if is_function_call(
                line,
                candidate,
            ):
                return "call"

            return "reference"

    target = query_info[
        "target"
    ]

    normalized_filename = normalize(
        os.path.basename(
            relative_path
        )
    )

    if (
        target
        and target in normalized_filename
    ):
        return "filename"

    normalized_path = normalize(
        relative_path
    )

    if (
        target
        and target in normalized_path
    ):
        return "path"

    if semantic_line_match(
        line,
        query_info,
    ):
        return "semantic"

    return "reference"


# ============================================================
# SCORE DEFINITION
# ============================================================

def score_definition(
    definition,
    query_info,
):

    if not definition:
        return 0

    score = 0

    name = definition[
        "name"
    ]

    normalized_name = normalize_identifier(
        name
    )

    identifier = identifier_form(
        name
    )

    target = query_info[
        "target"
    ]

    candidates = query_info[
        "candidates"
    ]

    target_tokens = query_info[
        "target_tokens"
    ]

    semantic_concepts = query_info.get(
        "semantic_concepts",
        [],
    )

    if identifier == target:

        score += 800

    elif identifier in candidates:

        score += 700

    elif normalized_name == target:

        score += 650

    for candidate in candidates:

        if normalize_identifier(
            candidate
        ) == normalized_name:

            score += 300

            break

    if (
        target
        and target in normalized_name
    ):

        score += 400

    definition_tokens = set(
        tokenize(name)
    )

    matched = sum(
        1
        for token in target_tokens
        if token in definition_tokens
    )

    score += matched * 80

    if (
        target_tokens
        and matched == len(
            target_tokens
        )
    ):

        score += 150

    semantic_matches = 0

    for concept in semantic_concepts:

        normalized_concept = normalize(
            concept
        )

        if (
            normalized_concept
            in normalized_name
        ):

            semantic_matches += 1

    score += semantic_matches * 25

    if definition[
        "type"
    ] == "function":

        score += 90

    elif definition[
        "type"
    ] == "class":

        score += 85

    if definition.get(
        "async",
        False,
    ):

        score += 10

    if definition.get(
        "parent"
    ):

        score += 20

    return score


# ============================================================
# MATCH TYPE SCORE
# ============================================================

def score_match_type(
    match_type,
    query_info,
):

    score = 0

    intent = query_info[
        "intent"
    ]

    operation = query_info.get(
        "operation",
        "general",
    )

    if match_type == "definition":

        score += 500

        if intent == "definition":
            score += 200

        elif intent == "location":
            score += 130

        elif intent == "general":
            score += 100

        if operation == "definition":
            score += 120

        if operation == "startup":
            score += 100

    elif match_type == "call":

        score += 300

        if intent == "reference":
            score += 120

        if operation == "call":
            score += 250

        if operation == "reference":
            score += 180

    elif match_type == "import":

        score += 270

        if intent == "reference":
            score += 130

        if operation == "import":
            score += 300

    elif match_type == "reference":

        score += 150

        if operation == "reference":
            score += 120

    elif match_type == "semantic":

        score += 80

        if operation == "general":
            score += 60

    elif match_type == "filename":

        score += 120

    elif match_type == "path":

        score += 80

    return score


# ============================================================
# EXACT TARGET SCORE
# ============================================================

def score_exact_target(
    line,
    query_info,
):

    score = 0

    candidates = query_info[
        "candidates"
    ]

    target = query_info[
        "target"
    ]

    for candidate in candidates:

        if contains_exact_identifier(
            line,
            candidate,
        ):

            score += 220

            if candidate == target:

                score += 100

            break

    normalized_line = normalize(
        line
    )

    if (
        target
        and target in normalized_line
    ):

        score += 50

    return score


# ============================================================
# SEMANTIC SCORE
# ============================================================

def score_semantic_match(
    line,
    query_info,
):

    return semantic_line_score(
        line,
        query_info,
    )


# ============================================================
# FILE PATH SCORE
# ============================================================

def score_path(
    filepath,
    query_info,
):

    score = 0

    relative_path = filepath.replace(
        "\\",
        "/",
    )

    filename = os.path.basename(
        relative_path
    )

    normalized_filename = normalize(
        filename
    )

    normalized_path = normalize(
        relative_path
    )

    target = query_info[
        "target"
    ]

    target_tokens = query_info[
        "target_tokens"
    ]

    semantic_concepts = query_info.get(
        "semantic_concepts",
        [],
    )

    if (
        target
        and target in normalized_filename
    ):

        score += 220

    if (
        target
        and target in normalized_path
    ):

        score += 110

    filename_tokens = set(
        tokenize(filename)
    )

    matched = sum(
        1
        for token in target_tokens
        if token in filename_tokens
    )

    score += matched * 45

    for concept in semantic_concepts:

        normalized_concept = normalize(
            concept
        )

        if (
            normalized_concept
            in normalized_filename
        ):

            score += 40

    return score


# ============================================================
# SOURCE DIRECTORY BONUS
# ============================================================

SOURCE_DIR_BONUS = {
    "ai_brain": 35,
    "core": 30,
    "system_layer": 25,
    "command_system": 25,
    "memory_layer": 25,
    "skills": 20,
    "gui": 20,
    "voice_engine": 20,
}


def score_source_directory(
    filepath
):

    relative_path = filepath.replace(
        "\\",
        "/",
    )

    first_directory = (
        relative_path.split(
            "/"
        )[0]
        if "/" in relative_path
        else ""
    )

    return SOURCE_DIR_BONUS.get(
        first_directory,
        0,
    )


# ============================================================
# SPECIAL FILE PENALTIES
# ============================================================

def calculate_file_penalty(
    filepath,
    project_path,
):

    penalty = 0

    normalized = filepath.replace(
        "\\",
        "/",
    ).lower()

    basename = os.path.basename(
        normalized
    )

    if is_test_file(
        filepath
    ):
        penalty += 180

    if is_documentation_file(
        filepath
    ):
        penalty += 120

    project_indexer_names = {
        "project_indexer.py",
        "project_indexer_v5_backup.py",
        "project_indexer_v6_backup.py",
        "project_indexer_v6_1_backup.py",
        "project_indexer_v6_2_backup.py",
        "project_indexer_v6_3_backup.py",
        "project_indexer_v6_4_backup.py",
        "project_indexer_v6_5_backup.py",
        "project_indexer_v6.1_backup.py",
        "project_indexer_v6.2_backup.py",
        "project_indexer_v6.3_backup.py",
        "project_indexer_v6.4_backup.py",
        "project_indexer_v6.5_backup.py",
    }

    if basename in project_indexer_names:

        penalty += 250

    if "backup" in basename:

        penalty += 120

    return penalty


# ============================================================
# LINE PENALTY
# ============================================================

def calculate_line_penalty(
    line
):

    penalty = 0

    if is_comment_line(
        line
    ):
        penalty += 100

    if is_docstring_line(
        line
    ):
        penalty += 120

    return penalty


# ============================================================
# USAGE BONUS
# ============================================================

def calculate_usage_bonus(
    line,
    query_info,
):

    score = 0

    target = query_info[
        "target"
    ]

    operation = query_info.get(
        "operation",
        "general",
    )

    if not target:
        return score

    for candidate in query_info[
        "candidates"
    ]:

        if is_function_call(
            line,
            candidate,
        ):

            score += 120

            if operation == "call":
                score += 220

            elif operation == "reference":
                score += 120

            break

    if detect_import_type(
        line
    ):

        score += 80

        if operation == "import":

            score += 220

    return score


# ============================================================
# STARTUP BONUS
# ============================================================

def calculate_startup_bonus(
    line,
    filepath,
    query_info,
):

    if query_info.get(
        "operation"
    ) != "startup":

        return 0

    score = 0

    normalized_line = normalize(
        line
    )

    normalized_file = normalize(
        filepath
    )

    startup_words = {
        "main",
        "start",
        "startup",
        "launch",
        "entry",
        "boot",
        "initialize",
        "run",
        "application",
        "assistant",
    }

    for word in startup_words:

        if word in normalized_line:
            score += 25

        if word in normalized_file:
            score += 15

    if (
        "__name__"
        in line
        and "__main__"
        in line
    ):

        score += 400

    return score


# ============================================================
# V6.6 RELATIONSHIP SCORE
# ============================================================

def calculate_relationship_score(
    filepath,
    line_number,
    line,
    query_info,
    relationship_data,
):

    operation = query_info.get(
        "operation",
        "general",
    )

    target = query_info.get(
        "target",
        "",
    )

    if not target:
        return 0

    score = 0

    normalized_targets = {
        normalize_identifier(
            candidate
        )
        for candidate in query_info.get(
            "candidates",
            [],
        )
    }

    normalized_targets.add(
        normalize_identifier(
            target
        )
    )

    if operation in {
        "reference",
        "call",
    }:

        for call in relationship_data.get(
            "calls",
            []
        ):

            callee = normalize_identifier(
                call.get(
                    "callee",
                    "",
                )
            )

            caller = normalize_identifier(
                call.get(
                    "caller",
                    "",
                )
            )

            if operation == "reference":

                if callee in normalized_targets:

                    if (
                        call.get(
                            "line"
                        )
                        == line_number
                    ):

                        score += 450

            elif operation == "call":

                if caller in normalized_targets:

                    if (
                        call.get(
                            "line"
                        )
                        == line_number
                    ):

                        score += 450

    if operation == "import":

        for import_info in relationship_data.get(
            "imports",
            []
        ):

            names = {
                normalize_identifier(
                    str(
                        import_info.get(
                            key,
                            "",
                        )
                    )
                )
                for key in (
                    "name",
                    "module",
                    "imported",
                    "full_name",
                )
            }

            if names.intersection(
                normalized_targets
            ):

                if (
                    import_info.get(
                        "line"
                    )
                    == line_number
                ):

                    score += 500

    return score


# ============================================================
# COMPLETE SCORE
# ============================================================

def calculate_score(
    filepath,
    line,
    query,
    query_info,
    definition=None,
    match_type="reference",
    project_path=None,
    relationship_data=None,
    line_number=None,
):

    score = 0

    if definition:

        score += score_definition(
            definition,
            query_info,
        )

    score += score_match_type(
        match_type,
        query_info,
    )

    score += score_exact_target(
        line,
        query_info,
    )

    score += score_semantic_match(
        line,
        query_info,
    )

    score += score_path(
        filepath,
        query_info,
    )

    score += score_source_directory(
        filepath
    )

    score += calculate_usage_bonus(
        line,
        query_info,
    )

    score += calculate_startup_bonus(
        line,
        filepath,
        query_info,
    )

    if relationship_data is not None:

        score += calculate_relationship_score(
            filepath,
            line_number,
            line,
            query_info,
            relationship_data,
        )

    target_tokens = query_info[
        "target_tokens"
    ]

    normalized_line = normalize(
        line
    )

    normalized_filename = normalize(
        os.path.basename(
            filepath
        )
    )

    normalized_path = normalize(
        filepath
    )

    line_matches = sum(
        1
        for token in target_tokens
        if token in normalized_line
    )

    filename_matches = sum(
        1
        for token in target_tokens
        if token in normalized_filename
    )

    path_matches = sum(
        1
        for token in target_tokens
        if token in normalized_path
    )

    score += line_matches * 15
    score += filename_matches * 25
    score += path_matches * 10

    if (
        target_tokens
        and all(
            token in normalized_line
            for token in target_tokens
        )
    ):

        score += 50

    intent = query_info[
        "intent"
    ]

    operation = query_info.get(
        "operation",
        "general",
    )

    if intent == "definition":

        if match_type == "definition":
            score += 200
        else:
            score -= 40

    elif intent == "reference":

        if match_type in {
            "reference",
            "call",
            "import",
        }:

            score += 100

        elif match_type == "definition":

            score += 20

    elif intent == "location":

        if match_type == "definition":

            score += 110

        elif match_type in {
            "filename",
            "path",
        }:

            score += 70

    if operation == "definition":

        if match_type == "definition":

            score += 200

        elif match_type in {
            "call",
            "import",
            "reference",
        }:

            score -= 30

    elif operation == "reference":

        if match_type in {
            "call",
            "reference",
            "import",
        }:

            score += 180

        elif match_type == "definition":

            score -= 50

    elif operation == "call":

        if match_type == "call":

            score += 300

        elif match_type == "definition":

            score -= 100

    elif operation == "import":

        if match_type == "import":

            score += 320

        elif match_type == "definition":

            score -= 120

    elif operation == "startup":

        if (
            "__main__"
            in line
        ):

            score += 400

        if match_type == "definition":

            score += 120

    if match_type == "semantic":

        if operation == "general":

            score += 70

        elif operation == "definition":

            score -= 30

    score -= calculate_line_penalty(
        line
    )

    if project_path is None:
        project_path = "."

    score -= calculate_file_penalty(
        filepath,
        project_path,
    )

    basename = os.path.basename(
        filepath
    ).lower()

    if (
        basename == "project_indexer.py"
        and match_type not in {
            "definition",
            "call",
            "import",
        }
    ):

        score -= 100

    return score


# ============================================================
# FUNCTION CONTEXT
# ============================================================

def find_enclosing_definition(
    definitions,
    line_number,
):

    candidates = []

    for definition_line, definition in (
        definitions.items()
    ):

        if definition_line <= line_number:

            end_line = definition.get(
                "end_line",
                definition_line,
            )

            if (
                line_number
                <= end_line
            ):

                candidates.append(
                    (
                        definition_line,
                        definition,
                    )
                )

    if not candidates:

        # Backward-compatible fallback.
        for definition_line, definition in (
            definitions.items()
        ):

            if definition_line <= line_number:

                candidates.append(
                    (
                        definition_line,
                        definition,
                    )
                )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return candidates[0][1]


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

    for i in range(
        start,
        end,
    ):

        snippet.append(
            f"{i + 1:4} | "
            f"{lines[i].rstrip()}"
        )

    return "\n".join(
        snippet
    )


# ============================================================
# PROJECT INDEX
# ============================================================

def build_project_index(
    project_path="."
):

    index = {}

    project_path = os.path.abspath(
        project_path
    )

    print(
        "Building project index..."
    )

    for root, dirs, files in os.walk(
        project_path
    ):

        dirs[:] = [
            directory
            for directory in dirs
            if not should_ignore_directory(
                directory
            )
        ]

        for file in files:

            if not is_allowed_file(
                file
            ):
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

                index[
                    relative_path
                ] = code

            except Exception as e:

                print(
                    f"Could not read "
                    f"{full_path}: {e}"
                )

    return index


# ============================================================
# QUALITY CONFIGURATION
# ============================================================

MIN_RESULT_SCORE = 20

SELF_INDEXER_PENALTY = 250
DOCUMENTATION_PENALTY = 120
COMMENT_PENALTY = 100
DOCSTRING_PENALTY = 120
TEST_FILE_PENALTY = 180

MAX_RESULTS = 15


# ============================================================
# RESULT QUALITY
# ============================================================

def is_quality_result(
    score,
    match_type,
    line,
    definition,
    query_info,
):

    if score < MIN_RESULT_SCORE:
        return False

    if definition:
        return True

    if is_comment_line(
        line
    ):

        return score >= 180

    if is_docstring_line(
        line
    ):

        return score >= 220

    if match_type == "semantic":

        return score >= 80

    if (
        match_type == "reference"
        and query_info.get(
            "operation"
        ) in {
            "reference",
            "call",
            "import",
        }
    ):

        return score >= 60

    return True


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_results(
    results
):

    unique = []

    seen = set()

    for result in results:

        key = (
            result["file"],
            result["line"],
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique.append(
            result
        )

    return unique


# ============================================================
# DEFINITION FILTER
# ============================================================

def filter_definition_intent(
    results,
    query_info,
):

    intent = query_info[
        "intent"
    ]

    operation = query_info.get(
        "operation",
        "general",
    )

    if (
        intent != "definition"
        and operation != "definition"
    ):

        return results

    definitions = [
        result
        for result in results
        if result["match"]
        == "definition"
    ]

    if definitions:

        other_results = [
            result
            for result in results
            if result["match"]
            != "definition"
        ]

        return (
            definitions
            + other_results
        )

    return results


# ============================================================
# REFERENCE FILTER
# ============================================================

def filter_reference_intent(
    results,
    query_info,
):

    operation = query_info.get(
        "operation",
        "general",
    )

    if operation not in {
        "reference",
        "call",
        "import",
    }:

        return results

    preferred = []
    secondary = []

    for result in results:

        if operation == "call":

            if result["match"] == "call":

                preferred.append(
                    result
                )

            else:

                secondary.append(
                    result
                )

        elif operation == "import":

            if result["match"] == "import":

                preferred.append(
                    result
                )

            else:

                secondary.append(
                    result
                )

        else:

            if result["match"] in {
                "call",
                "reference",
                "import",
            }:

                preferred.append(
                    result
                )

            else:

                secondary.append(
                    result
                )

    return preferred + secondary


# ============================================================
# V6.6 RELATIONSHIP FILTER
# ============================================================

def filter_relationship_results(
    results,
    query_info,
):

    operation = query_info.get(
        "operation",
        "general",
    )

    if operation not in {
        "reference",
        "call",
        "import",
    }:

        return results

    relationship_results = []
    normal_results = []

    for result in results:

        relationship_score = result.get(
            "relationship_score",
            0,
        )

        if relationship_score > 0:

            relationship_results.append(
                result
            )

        else:

            normal_results.append(
                result
            )

    relationship_results.sort(
        key=lambda item: (
            item.get(
                "relationship_score",
                0,
            ),
            item.get(
                "score",
                0,
            ),
        ),
        reverse=True,
    )

    return (
        relationship_results
        + normal_results
    )


# ============================================================
# SELF INDEXER FILTER
# ============================================================

def suppress_self_indexer_noise(
    results
):

    filtered = []

    for result in results:

        filename = os.path.basename(
            result["file"]
        ).lower()

        if (
            filename == "project_indexer.py"
            and result["match"]
            not in {
                "definition",
                "call",
                "import",
            }
        ):

            if result["score"] < 500:
                continue

        filtered.append(
            result
        )

    return filtered


# ============================================================
# SORT RESULTS
# ============================================================

def sort_results(
    results
):

    results.sort(
        key=lambda result: (
            result["score"],

            result.get(
                "relationship_score",
                0,
            ),

            result.get(
                "semantic_score",
                0,
            ),

            1
            if result["match"]
            == "definition"
            else 0,

            1
            if result["match"]
            == "call"
            else 0,

            1
            if result["match"]
            == "import"
            else 0,

            1
            if result["match"]
            == "reference"
            else 0,

            -result["line"],
        ),
        reverse=True,
    )

    return results


# ============================================================
# QUERY DEBUG
# ============================================================

def print_query_analysis(
    query_info
):

    print(
        f"[V6.6 QUERY] "
        f"original={query_info['original']!r} "
        f"| normalized={query_info['normalized']!r} "
        f"| intent={query_info['intent']} "
        f"| operation={query_info['operation']} "
        f"| target={query_info['target']!r} "
        f"| target_tokens={query_info['target_tokens']!r}"
    )

    print(
        f"[V6.6 ROLES] "
        f"{query_info.get('roles', {})!r}"
    )

    print(
        f"[V6.6 CANDIDATES] "
        f"{query_info['candidates']!r}"
    )

    if query_info.get(
        "semantic_concepts"
    ):

        print(
            f"[V6.6 SEMANTIC] "
            f"{query_info['semantic_concepts']!r}"
        )


# ============================================================
# RELATIONSHIP DEBUG
# ============================================================

def print_relationship_debug(
    query_info,
    relationship_index,
):

    operation = query_info.get(
        "operation"
    )

    target = query_info.get(
        "target"
    )

    if operation not in {
        "reference",
        "call",
        "import",
    }:

        return

    print(
        f"[V6.6 RELATIONSHIP] "
        f"operation={operation} "
        f"| target={target!r}"
    )

    normalized_targets = {
        normalize_identifier(
            candidate
        )
        for candidate in query_info.get(
            "candidates",
            [],
        )
    }

    normalized_targets.add(
        normalize_identifier(
            target
        )
    )

    if operation == "reference":

        for target_name in normalized_targets:

            matches = relationship_index[
                "callers"
            ].get(
                target_name,
                [],
            )

            if matches:

                print(
                    f"[V6.6 CALLERS] "
                    f"{target_name}: "
                    f"{len(matches)}"
                )

    elif operation == "call":

        for target_name in normalized_targets:

            matches = relationship_index[
                "callees"
            ].get(
                target_name,
                [],
            )

            if matches:

                print(
                    f"[V6.6 CALLEES] "
                    f"{target_name}: "
                    f"{len(matches)}"
                )

    elif operation == "import":

        for target_name in normalized_targets:

            matches = relationship_index[
                "imports"
            ].get(
                target_name,
                [],
            )

            if matches:

                print(
                    f"[V6.6 IMPORTS] "
                    f"{target_name}: "
                    f"{len(matches)}"
                )


# ============================================================
# SEARCH CODE V6.6
# ============================================================

def search_code(
    project_path,
    query,
    context=5,
):

    """
    Search project source files.

    V6.6 examples:

        search_code(
            ".",
            "where is process command",
        )

        search_code(
            ".",
            "what calls process_command",
        )

        search_code(
            ".",
            "who uses process_command",
        )

        search_code(
            ".",
            "where is process_command imported",
        )

        search_code(
            ".",
            "show imports of process_command",
        )

        search_code(
            ".",
            "where does Jarvis start",
        )

        search_code(
            ".",
            "where is the GUI created",
        )

        search_code(
            ".",
            "find the code that handles microphone",
        )

        search_code(
            ".",
            "where is volume control",
        )

        search_code(
            ".",
            "find the code related to memory",
        )

        search_code(
            ".",
            "what does process_command call",
        )

        V6.6 relationship queries:

        search_code(
            ".",
            "who calls process_command",
        )

        search_code(
            ".",
            "what does process_command call",
        )

        search_code(
            ".",
            "what imports pyttsx3",
        )
    """

    results = []

    # ========================================================
    # QUERY ANALYSIS
    # ========================================================

    query_info = analyze_query(
        query
    )

    normalized_query = query_info[
        "normalized"
    ]

    target = query_info[
        "target"
    ]

    candidates = query_info[
        "candidates"
    ]

    intent = query_info[
        "intent"
    ]

    operation = query_info[
        "operation"
    ]

    if not normalized_query:
        return results

    if (
        not candidates
        and not query_info.get(
            "semantic_concepts"
        )
    ):

        return results

    print_query_analysis(
        query_info
    )

    # ========================================================
    # PROJECT
    # ========================================================

    project_path = os.path.abspath(
        project_path
    )

    # ========================================================
    # RELATIONSHIP INDEX
    # ========================================================

    relationship_index = (
        build_relationship_index(
            project_path
        )
    )

    print_relationship_debug(
        query_info,
        relationship_index,
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
            if not should_ignore_directory(
                directory
            )
        ]

        for file in files:

            if not is_allowed_file(
                file
            ):

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
            # READ
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
                    f"Could not search "
                    f"{filepath}: {e}"
                )

                continue

            # =================================================
            # AST
            # =================================================

            if filepath.lower().endswith(
                ".py"
            ):

                definitions = (
                    extract_python_structure(
                        lines
                    )
                )

                relationship_data = (
                    relationship_index[
                        "files"
                    ].get(
                        relative_path,
                        {},
                    )
                )

            else:

                definitions = {}
                relationship_data = {}

            # =================================================
            # SEARCH LINES
            # =================================================

            for i, line in enumerate(
                lines
            ):

                line_number = i + 1

                stripped = line.strip()

                if not stripped:
                    continue

                definition = definitions.get(
                    line_number
                )

                # ------------------------------------------------
                # Definition
                # ------------------------------------------------

                definition_match = (
                    definition is not None
                    and target_matches_definition(
                        definition,
                        query_info,
                    )
                )

                # ------------------------------------------------
                # Exact target
                # ------------------------------------------------

                exact_identifier_match = False

                matched_candidate = None

                for candidate in candidates:

                    if contains_exact_identifier(
                        line,
                        candidate,
                    ):

                        exact_identifier_match = True
                        matched_candidate = candidate
                        break

                # ------------------------------------------------
                # Path
                # ------------------------------------------------

                normalized_path = normalize(
                    relative_path
                )

                normalized_filename = normalize(
                    file
                )

                path_match = (
                    bool(target)
                    and target
                    in normalized_path
                )

                filename_match = (
                    bool(target)
                    and target
                    in normalized_filename
                )

                # ------------------------------------------------
                # Text
                # ------------------------------------------------

                normalized_line = normalize(
                    line
                )

                textual_target_match = (
                    bool(target)
                    and target
                    in normalized_line
                )

                # ------------------------------------------------
                # Semantic
                # ------------------------------------------------

                semantic_match = (
                    semantic_line_match(
                        line,
                        query_info,
                    )
                )

                # ------------------------------------------------
                # Relationship
                # ------------------------------------------------

                relationship_score = (
                    calculate_relationship_score(
                        relative_path,
                        line_number,
                        line,
                        query_info,
                        relationship_data,
                    )
                )

                # =================================================
                # RELATIONSHIP-ONLY MATCH
                # =================================================

                relationship_match = (
                    relationship_score > 0
                )

                # =================================================
                # IGNORE UNRELATED
                # =================================================

                if not (
                    definition_match
                    or exact_identifier_match
                    or filename_match
                    or path_match
                    or textual_target_match
                    or semantic_match
                    or relationship_match
                ):

                    continue

                # =================================================
                # COMMENT
                # =================================================

                if (
                    not definition_match
                    and not relationship_match
                    and is_comment_line(
                        line
                    )
                ):

                    continue

                # =================================================
                # DOCUMENTATION
                # =================================================

                if (
                    not definition_match
                    and not relationship_match
                    and is_documentation_file(
                        filepath
                    )
                ):

                    if not exact_identifier_match:
                        continue

                # =================================================
                # MATCH TYPE
                # =================================================

                match_type = determine_match_type(
                    line,
                    definition
                    if definition_match
                    else None,
                    query_info,
                    relative_path,
                )

                # ------------------------------------------------
                # Relationship override.
                # ------------------------------------------------

                if relationship_match:

                    if operation == "call":

                        match_type = "call"

                    elif operation == "reference":

                        match_type = "call"

                    elif operation == "import":

                        match_type = "import"

                # ------------------------------------------------
                # Semantic fallback.
                # ------------------------------------------------

                if (
                    match_type == "reference"
                    and semantic_match
                    and not exact_identifier_match
                    and not textual_target_match
                    and not definition_match
                    and not relationship_match
                ):

                    match_type = "semantic"

                # =================================================
                # SCORE
                # =================================================

                score = calculate_score(
                    relative_path,
                    line,
                    query,
                    query_info,
                    definition
                    if definition_match
                    else None,
                    match_type,
                    project_path,
                    relationship_data,
                    line_number,
                )

                # Definition bonus.
                if definition_match:
                    score += 120

                # Exact bonus.
                if exact_identifier_match:
                    score += 120

                # Filename bonus.
                if filename_match:
                    score += 70

                # Path bonus.
                if path_match:
                    score += 30

                # Semantic bonus.
                if semantic_match:
                    score += 30

                # Relationship bonus.
                if relationship_match:
                    score += relationship_score

                # =================================================
                # FUNCTION CONTEXT
                # =================================================

                enclosing_definition = (
                    find_enclosing_definition(
                        definitions,
                        line_number,
                    )
                )

                function_context = None
                class_context = None

                if enclosing_definition:

                    if enclosing_definition[
                        "type"
                    ] == "function":

                        function_context = (
                            enclosing_definition[
                                "name"
                            ]
                        )

                        class_context = (
                            enclosing_definition.get(
                                "parent"
                            )
                        )

                    elif enclosing_definition[
                        "type"
                    ] == "class":

                        class_context = (
                            enclosing_definition[
                                "name"
                            ]
                        )

                # =================================================
                # OPERATION-AWARE FUNCTION RANKING
                # =================================================

                if (
                    function_context
                    and operation in {
                        "reference",
                        "call",
                        "import",
                    }
                ):

                    score += 35

                if (
                    function_context
                    and operation == "definition"
                ):

                    score += 25

                if (
                    class_context
                    and operation in {
                        "reference",
                        "call",
                    }
                ):

                    score += 15

                # =================================================
                # QUALITY
                # =================================================

                if not is_quality_result(
                    score,
                    match_type,
                    line,
                    definition
                    if definition_match
                    else None,
                    query_info,
                ):

                    continue

                # =================================================
                # SNIPPET
                # =================================================

                snippet = build_snippet(
                    lines,
                    line_number,
                    context,
                )

                # =================================================
                # METADATA
                # =================================================

                if definition_match:

                    result_type = definition[
                        "type"
                    ]

                    result_name = definition[
                        "name"
                    ]

                    parent = definition.get(
                        "parent"
                    )

                    async_flag = definition.get(
                        "async",
                        False,
                    )

                else:

                    result_type = "reference"

                    result_name = None
                    parent = None
                    async_flag = False

                    if match_type == "import":

                        result_type = "import"

                    elif match_type == "call":

                        result_type = "reference"

                    elif match_type == "semantic":

                        result_type = "semantic"

                # =================================================
                # RELATIONSHIP DETAILS
                # =================================================

                relationship_type = (
                    query_info.get(
                        "relation",
                        RELATIONSHIP_TARGET,
                    )
                )

                relationship_target = None
                relationship_source = None

                for call in relationship_data.get(
                    "calls",
                    [],
                ):

                    if (
                        call.get(
                            "line"
                        )
                        != line_number
                    ):
                        continue

                    relationship_target = (
                        call.get(
                            "callee"
                        )
                    )

                    relationship_source = (
                        call.get(
                            "caller"
                        )
                    )

                    break

                import_relationship = None

                for import_info in relationship_data.get(
                    "imports",
                    [],
                ):

                    if (
                        import_info.get(
                            "line"
                        )
                        != line_number
                    ):
                        continue

                    import_relationship = (
                        import_info
                    )

                    break

                # =================================================
                # RESULT
                # =================================================

                result = {
                    "file": relative_path,
                    "line": line_number,
                    "snippet": snippet,
                    "score": score,
                    "match": match_type,
                    "intent": intent,
                    "operation": operation,
                    "type": result_type,
                    "name": result_name,
                    "parent": parent,
                    "async": async_flag,

                    # V6.5 compatibility.
                    "function": function_context,
                    "class": class_context,
                    "relation": relationship_type,
                    "semantic_score": (
                        semantic_line_score(
                            line,
                            query_info,
                        )
                    ),

                    # V6.6 additions.
                    "semantic_confidence": (
                        semantic_confidence(
                            line,
                            query_info,
                        )
                    ),
                    "relationship_score": (
                        relationship_score
                    ),
                    "relationship_type": (
                        relationship_type
                    ),
                    "relationship_source": (
                        relationship_source
                    ),
                    "relationship_target": (
                        relationship_target
                    ),
                    "matched_candidate": (
                        matched_candidate
                    ),
                    "import_relationship": (
                        import_relationship
                    ),
                }

                results.append(
                    result
                )

    # ========================================================
    # DEDUPLICATE
    # ========================================================

    results = deduplicate_results(
        results
    )

    # ========================================================
    # SELF INDEXER
    # ========================================================

    results = suppress_self_indexer_noise(
        results
    )

    # ========================================================
    # DEFINITION FILTER
    # ========================================================

    results = filter_definition_intent(
        results,
        query_info,
    )

    # ========================================================
    # REFERENCE FILTER
    # ========================================================

    results = filter_reference_intent(
        results,
        query_info,
    )

    # ========================================================
    # RELATIONSHIP FILTER
    # ========================================================

    results = filter_relationship_results(
        results,
        query_info,
    )

    # ========================================================
    # SORT
    # ========================================================

    results = sort_results(
        results
    )

    # ========================================================
    # DEBUG RANKING
    # ========================================================

    for result in results[
        :MAX_RESULTS
    ]:

        print(
            f"[V6.6 RANK] "
            f"{result['file']} "
            f"| line={result['line']} "
            f"| match={result['match']} "
            f"| type={result['type']} "
            f"| name={result['name']} "
            f"| function={result.get('function')} "
            f"| class={result.get('class')} "
            f"| relation={result.get('relation')} "
            f"| relationship="
            f"{result.get('relationship_source')}"
            f" -> "
            f"{result.get('relationship_target')} "
            f"| rel_score={result.get('relationship_score')} "
            f"| semantic="
            f"{result.get('semantic_confidence')} "
            f"| score={result['score']}"
        )

    # ========================================================
    # RETURN
    # ========================================================

    return results[
        :MAX_RESULTS
    ]


# ============================================================
# RELATIONSHIP SUMMARY
# ============================================================

def get_relationship_summary(
    project_path="."
):

    relationship_index = (
        build_relationship_index(
            project_path
        )
    )

    total_files = len(
        relationship_index[
            "files"
        ]
    )

    total_callers = sum(
        len(value)
        for value in relationship_index[
            "callers"
        ].values()
    )

    total_callees = sum(
        len(value)
        for value in relationship_index[
            "callees"
        ].values()
    )

    total_imports = sum(
        len(value)
        for value in relationship_index[
            "imports"
        ].values()
    )

    return {
        "files": total_files,
        "caller_relationships": total_callers,
        "callee_relationships": total_callees,
        "import_relationships": total_imports,
    }


# ============================================================
# OPTIONAL DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 75)
    print("PROJECT INDEXER V6.6")
    print("RELATIONSHIP INTELLIGENCE CODE SEARCH")
    print("=" * 75)
    print()

    project = "."

    # ========================================================
    # V6.3 / V6.4 / V6.5 COMPATIBILITY TESTS
    # ========================================================

    test_queries = [

        "process command",

        "where is process command",

        "show process_command function",

        "where is class Jarvis",

        "find process_command",

        "show me the function that handles process commands",

        "what calls process_command",

        "who uses process_command",

        "where is process_command imported",

        "show imports of process_command",

        "where does Jarvis start",

        "where is the GUI created",

        "find the code that handles microphone",

        "where is volume control",

        "find the code related to memory",

        "what does process_command call",

        "what invokes process_command",

        "who calls the microphone handler",

        "where is microphone processing",

        "where is voice input handled",

        "which function controls volume",

        "where is the GUI initialized",

        "what handles voice commands",

        "where is the assistant startup",

        "what uses the memory system",

        # ====================================================
        # V6.6 RELATIONSHIP TESTS
        # ====================================================

        "who calls process_command",

        "what does process_command call",

        "who invokes process_command",

        "what does the voice handler call",

        "what does the microphone handler call",

        "who uses the memory system",

        "what uses ask_ai",

        "where is pyttsx3 imported",

        "what imports speech_recognition",

        "where is customtkinter imported",

        "who calls speak",

        "what does speak call",

        "who calls listen",

        "what does listen call",

    ]

    # ========================================================
    # RELATIONSHIP SUMMARY
    # ========================================================

    try:

        summary = get_relationship_summary(
            project
        )

        print(
            "[V6.6 RELATIONSHIP SUMMARY]"
        )

        print(
            summary
        )

    except Exception as e:

        print(
            f"Could not build relationship "
            f"summary: {e}"
        )

    # ========================================================
    # SEARCH TESTS
    # ========================================================

    for query in test_queries:

        print()
        print("=" * 75)
        print(
            f"QUERY: {query}"
        )
        print("=" * 75)

        try:

            results = search_code(
                project,
                query,
            )

        except Exception as e:

            print(
                f"SEARCH ERROR: {e}"
            )

            continue

        print()

        if not results:

            print(
                "No results."
            )

            continue

        for result in results[
            :5
        ]:

            print(
                {
                    "file": result["file"],
                    "line": result["line"],
                    "match": result["match"],
                    "type": result["type"],
                    "name": result["name"],
                    "function": result.get(
                        "function"
                    ),
                    "class": result.get(
                        "class"
                    ),
                    "relation": result.get(
                        "relation"
                    ),
                    "relationship_type": result.get(
                        "relationship_type"
                    ),
                    "relationship_source": result.get(
                        "relationship_source"
                    ),
                    "relationship_target": result.get(
                        "relationship_target"
                    ),
                    "relationship_score": result.get(
                        "relationship_score"
                    ),
                    "semantic_confidence": result.get(
                        "semantic_confidence"
                    ),
                    "score": result["score"],
                }
            )

            print(
                result["snippet"]
            )

            print(
                "-" * 75
            )