"""
Stark Taskmaster & Persistent To-Do Directive Engine for J.A.R.V.I.S.
Stores and tracks active user directives in SQLite (jarvis_memory.db)
with live real-time HUD rendering.
"""

import sqlite3
import os
import time
from datetime import datetime
from typing import List, Dict, Any

from voice_engine.sound_effects import play_fx

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jarvis_memory.db")


def _init_todos_table():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    completed_at TEXT DEFAULT ''
                );
            """)
            conn.commit()
    except Exception as e:
        print(f"[TODO DB INIT ERROR]: {e}")

_init_todos_table()


def add_task(task_text: str) -> str:
    """Add a new task directive."""
    clean_text = task_text.strip()
    if not clean_text:
        return "Please specify the task description, Sir."

    now = datetime.now().isoformat()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO todos (task, status, created_at) VALUES (?, 'pending', ?);",
                (clean_text, now)
            )
            conn.commit()
            task_id = cursor.lastrowid

        play_fx("complete")
        return f"Directive added: '{clean_text}' logged as task number {task_id}, Sir."
    except Exception as e:
        print(f"[TODO ADD ERROR]: {e}")
        return f"Failed to log task directive: {e}"


def get_active_tasks(limit: int = 5) -> List[Dict[str, Any]]:
    """Get list of active pending task directives for HUD display."""
    tasks = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, task, status, created_at FROM todos WHERE status = 'pending' ORDER BY id ASC LIMIT ?;",
                (limit,)
            )
            for row in cursor.fetchall():
                tasks.append({
                    "id": row["id"],
                    "task": row["task"],
                    "status": row["status"]
                })
    except Exception as e:
        print(f"[TODO FETCH ERROR]: {e}")
    return tasks


def complete_task(identifier: str) -> str:
    """Mark a task directive as completed by ID number or substring match."""
    clean_id = identifier.strip().lower()
    now = datetime.now().isoformat()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # 1. Try numeric ID
            if clean_id.isdigit():
                tid = int(clean_id)
                cursor.execute(
                    "UPDATE todos SET status = 'completed', completed_at = ? WHERE id = ? AND status = 'pending';",
                    (now, tid)
                )
                if cursor.rowcount > 0:
                    conn.commit()
                    play_fx("complete")
                    return f"Task directive {tid} marked as completed, Sir."

            # 2. Try substring match
            cursor.execute(
                "SELECT id, task FROM todos WHERE status = 'pending' AND LOWER(task) LIKE ? LIMIT 1;",
                (f"%{clean_id}%",)
            )
            row = cursor.fetchone()
            if row:
                tid, task_name = row[0], row[1]
                cursor.execute(
                    "UPDATE todos SET status = 'completed', completed_at = ? WHERE id = ?;",
                    (now, tid)
                )
                conn.commit()
                play_fx("complete")
                return f"Completed directive: '{task_name}', Sir. Well done."

        return f"I could not locate an active pending task matching '{identifier}', Sir."

    except Exception as e:
        print(f"[TODO COMPLETE ERROR]: {e}")
        return f"Failed to complete task: {e}"


def list_tasks_summary() -> str:
    """Generate spoken summary of active pending tasks."""
    active = get_active_tasks(limit=10)
    if not active:
        return "You have zero pending task directives, Sir. All objectives are clear."

    if len(active) == 1:
        return f"You have 1 pending directive: '{active[0]['task']}'."

    task_list_str = "; ".join([f"Task {t['id']}: {t['task']}" for t in active[:4]])
    return f"You have {len(active)} active directives: {task_list_str}."


def clear_completed_tasks() -> str:
    """Purge completed directives."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM todos WHERE status = 'completed';")
            count = cursor.rowcount
            conn.commit()
        return f"Purged {count} completed directives from archive, Sir."
    except Exception as e:
        return f"Failed to purge completed tasks: {e}"
