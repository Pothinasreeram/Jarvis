"""
JARVIS Long-Term Semantic Memory Engine
Powered by SQLite3 + FTS5 Full-Text Indexing + BM25 Relevance Ranking.
Provides sub-millisecond retrieval, persistent memory across restarts,
and automatic context injection for AI inference.
"""

import os
import json
import sqlite3
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jarvis_memory.db")
LEGACY_MEMORY_JSON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory.json")


def _get_connection():
    """Get thread-safe connection to the SQLite memory database."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_memory_db():
    """Initialize SQLite database tables, FTS5 virtual tables, and sync triggers."""
    with _get_connection() as conn:
        cursor = conn.cursor()

        # Primary storage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL DEFAULT 'user_fact',
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                context TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # FTS5 Virtual table for ultra-fast full-text search with BM25 ranking
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                key,
                value,
                category,
                context,
                tokenize = 'porter unicode61'
            );
        """)

        # Triggers to keep FTS5 synchronized with primary table
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, key, value, category, context)
                VALUES (new.id, new.key, new.value, new.category, new.context);
            END;
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_memories_ad AFTER DELETE ON memories BEGIN
                DELETE FROM memories_fts WHERE rowid = old.id;
            END;
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_memories_au AFTER UPDATE ON memories BEGIN
                DELETE FROM memories_fts WHERE rowid = old.id;
                INSERT INTO memories_fts(rowid, key, value, category, context)
                VALUES (new.id, new.key, new.value, new.category, new.context);
            END;
        """)

        conn.commit()

    # Migrate from legacy memory.json if present
    _migrate_from_json()


def _migrate_from_json():
    """Seamlessly migrate any existing facts from memory.json into SQLite."""
    if not os.path.exists(LEGACY_MEMORY_JSON):
        return

    try:
        with open(LEGACY_MEMORY_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        entities = data.get("entities", {})
        for ent_name, ent_data in entities.items():
            if ent_name == "current":
                continue
            facts = ent_data.get("facts", {}) if isinstance(ent_data, dict) else {}
            for f_key, f_val in facts.items():
                store_fact(f"{ent_name} {f_key}".strip(), str(f_val), category="entity_fact")

        # Top-level name or keys
        if "name" in data and data["name"]:
            store_fact("user_name", data["name"], category="user_preference")

    except Exception as e:
        print(f"[MEMORY MIGRATION ERROR]: {e}")


def store_fact(key: str, value: str, category: str = "user_fact", context: str = "") -> str:
    """
    Store or update a fact in long-term memory.
    """
    clean_key = key.strip().lower()
    clean_val = value.strip()
    if not clean_key or not clean_val:
        return "Invalid memory key or value."

    now = datetime.now().isoformat()

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO memories (category, key, value, context, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                category = excluded.category,
                context = excluded.context,
                updated_at = excluded.updated_at;
        """, (category, clean_key, clean_val, context, now, now))
        conn.commit()

    return f"Remembered: {clean_key} is {clean_val}"


def recall_fact(key: str) -> Optional[str]:
    """Retrieve exact fact by key, or return None."""
    clean_key = key.strip().lower()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM memories WHERE key = ? LIMIT 1;", (clean_key,))
        row = cursor.fetchone()
        if row:
            return row[0]
    return None


def delete_fact(key: str) -> bool:
    """Delete a fact from long-term memory."""
    clean_key = key.strip().lower()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE key = ?;", (clean_key,))
        conn.commit()
        return cursor.rowcount > 0


def get_all_facts(category: Optional[str] = None) -> List[Dict[str, str]]:
    """Retrieve all stored facts, optionally filtered by category."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT key, value, category, updated_at FROM memories WHERE category = ? ORDER BY key ASC;", (category,))
        else:
            cursor.execute("SELECT key, value, category, updated_at FROM memories ORDER BY category ASC, key ASC;")
        rows = cursor.fetchall()
        return [{"key": r[0], "value": r[1], "category": r[2], "updated_at": r[3]} for r in rows]


def search_memory(query: str, limit: int = 5) -> List[Dict[str, str]]:
    """
    Perform sub-millisecond FTS5 search with BM25 relevance ranking.
    Falls back to LIKE search if FTS syntax query yields empty.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    # Clean words for FTS5 (remove punctuation, quote each word with wildcard)
    words = re.findall(r'\b[A-Za-z0-9_]+\b', clean_query)
    # Filter common stop words for memory search
    stop_words = {"who", "what", "where", "when", "why", "how", "is", "are", "the", "a", "an", "do", "you", "my", "your", "tell", "me", "about"}
    filtered_words = [w for w in words if w.lower() not in stop_words]

    if not filtered_words:
        filtered_words = words

    if not filtered_words:
        return []

    fts_expression = " OR ".join(f"{w}*" for w in filtered_words)

    results = []
    with _get_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT m.key, m.value, m.category, bm25(memories_fts) as rank
                FROM memories_fts f
                JOIN memories m ON f.rowid = m.id
                WHERE memories_fts MATCH ?
                ORDER BY rank
                LIMIT ?;
            """, (fts_expression, limit))
            rows = cursor.fetchall()
            for r in rows:
                results.append({"key": r[0], "value": r[1], "category": r[2], "score": r[3]})
        except Exception as e:
            # Fallback to standard LIKE search
            pass

        if not results:
            for w in filtered_words[:3]:
                cursor.execute("""
                    SELECT key, value, category, 0 as rank
                    FROM memories
                    WHERE key LIKE ? OR value LIKE ?
                    LIMIT ?;
                """, (f"%{w}%", f"%{w}%", limit))
                for r in cursor.fetchall():
                    if not any(res["key"] == r[0] for res in results):
                        results.append({"key": r[0], "value": r[1], "category": r[2], "score": 0})

    return results[:limit]


def get_memory_context_for_prompt(prompt: str) -> str:
    """
    Build a high-signal memory context string to inject directly into the AI Brain system prompt.
    Includes persistent core user facts + relevant semantic matches.
    """
    all_facts = get_all_facts()
    if not all_facts:
        return ""

    context_lines = []

    # 1. Always include core user identity facts (e.g. name, preferences)
    core_keys = {"name", "user_name", "user", "job", "profession", "city", "location", "language", "favorite"}
    core_facts = [f for f in all_facts if any(k in f["key"] for k in core_keys)]

    if core_facts:
        context_lines.append("CORE USER PROFILE:")
        for f in core_facts[:6]:
            context_lines.append(f"- {f['key'].replace('_', ' ').title()}: {f['value']}")

    # 2. Search for relevant facts matching the user's current prompt
    matched = search_memory(prompt, limit=4)
    relevant = [m for m in matched if not any(cf["key"] == m["key"] for cf in core_facts)]

    if relevant:
        context_lines.append("\nRELEVANT FACTS FROM LONG-TERM MEMORY:")
        for r in relevant:
            context_lines.append(f"- {r['key'].replace('_', ' ').title()}: {r['value']}")

    return "\n".join(context_lines)


def parse_memory_command(text: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse a voice command instructing Jarvis to remember something.
    Returns (action, key, value) or None.
    e.g.
      "remember that my dog's name is Max" -> ("remember", "dog's name", "Max")
      "remember my email is test@example.com" -> ("remember", "email", "test@example.com")
      "what do you remember about me" -> ("summary", "", "")
      "forget my dog's name" -> ("forget", "dog's name", "")
    """
    cleaned = text.strip()
    lowered = cleaned.lower()

    # Query all facts
    if any(q in lowered for q in [
        "what do you remember about me",
        "what do you know about me",
        "what do you remember",
        "tell me what you remember",
        "list your memories",
        "show memory"
    ]):
        return ("summary", "", "")

    # Forget fact
    forget_patterns = [
        r"forget that (.+)",
        r"forget my (.+)",
        r"forget (.+)"
    ]
    for p in forget_patterns:
        m = re.match(p, lowered)
        if m:
            key = m.group(1).replace("is", "").strip()
            return ("forget", key, "")

    # Remember patterns
    remember_patterns = [
        r"(?:jarvis\s+)?(?:please\s+)?remember\s+that\s+(?:my\s+)?(.+?)\s+(?:is|are|=|was)\s+(.+)",
        r"(?:jarvis\s+)?(?:please\s+)?remember\s+(?:my\s+)?(.+?)\s+(?:is|are|=|was)\s+(.+)",
        r"(?:jarvis\s+)?(?:please\s+)?remember\s+that\s+i\s+(?:like|prefer|am|work as|live in)\s+(.+)",
        r"(?:jarvis\s+)?(?:please\s+)?remember\s+(.+)"
    ]

    for i, p in enumerate(remember_patterns):
        m = re.match(p, cleaned, re.IGNORECASE)
        if m:
            if i == 0 or i == 1:
                key = m.group(1).strip()
                val = m.group(2).strip()
                return ("remember", key, val)
            elif i == 2:
                verb = "preference"
                val = m.group(1).strip()
                return ("remember", "preference", val)
            elif i == 3:
                content = m.group(1).strip()
                if " is " in content:
                    parts = content.split(" is ", 1)
                    return ("remember", parts[0].strip(), parts[1].strip())
                return ("remember", "note", content)

    return None


# Auto-initialize database on module import
init_memory_db()
