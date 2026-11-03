"""
J.A.R.V.I.S. Autonomous Engineering Agency - Persistent Project Database
Stores enterprise projects, multi-day sprints, agent task boards, code artifacts,
and daily standup logs using SQLite WAL mode.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "jarvis_projects.db")


def _get_connection():
    """Get thread-safe connection to the SQLite projects database."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_agency_db():
    """Initialize database tables for autonomous multi-day agile project execution."""
    with _get_connection() as conn:
        cursor = conn.cursor()

        # 1. Projects master table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                client_objective TEXT NOT NULL,
                current_sprint INTEGER DEFAULT 0,
                total_sprints INTEGER DEFAULT 5,
                status TEXT NOT NULL DEFAULT 'intake',
                root_dir TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # 2. Sprints table (multi-day development phases)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                sprint_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                deliverables_summary TEXT DEFAULT '',
                review_notes TEXT DEFAULT '',
                started_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                UNIQUE (project_id, sprint_number)
            );
        """)

        # 3. Tasks / Kanban board table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                sprint_number INTEGER NOT NULL,
                assigned_agent TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'todo',
                result_summary TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
        """)

        # 4. Project Artifacts table (PRD, Architecture, Code, Tests, Readme)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                sprint_number INTEGER NOT NULL,
                artifact_type TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
        """)

        # 5. Standup logs (daily progress reports for Morning Briefing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS standup_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                sprint_number INTEGER NOT NULL,
                agent_name TEXT NOT NULL,
                yesterday_work TEXT NOT NULL,
                today_plan TEXT NOT NULL,
                blockers TEXT DEFAULT 'None',
                timestamp TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
        """)

        conn.commit()


# ============================================================
# PROJECT CRUD
# ============================================================

def create_project_record(name: str, client_objective: str, root_dir: str, metadata: Optional[Dict[str, Any]] = None) -> int:
    """Create a new project entry and return its ID."""
    clean_name = name.strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_json = json.dumps(metadata or {})

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO projects (name, client_objective, root_dir, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                client_objective = excluded.client_objective,
                updated_at = excluded.updated_at;
        """, (clean_name, client_objective.strip(), root_dir, meta_json, now, now))
        conn.commit()
        return cursor.lastrowid or get_project_by_name(clean_name)["id"]


def get_project_by_id(project_id: int) -> Optional[Dict[str, Any]]:
    """Fetch project details by ID."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, client_objective, current_sprint, total_sprints, status, root_dir, metadata, created_at, updated_at FROM projects WHERE id = ?;", (project_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "client_objective": row[2],
            "current_sprint": row[3],
            "total_sprints": row[4],
            "status": row[5],
            "root_dir": row[6],
            "metadata": json.loads(row[7]) if row[7] else {},
            "created_at": row[8],
            "updated_at": row[9]
        }


def get_project_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Fetch project details by unique project name."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, client_objective, current_sprint, total_sprints, status, root_dir, metadata, created_at, updated_at FROM projects WHERE LOWER(name) = LOWER(?);", (name.strip(),))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "client_objective": row[2],
            "current_sprint": row[3],
            "total_sprints": row[4],
            "status": row[5],
            "root_dir": row[6],
            "metadata": json.loads(row[7]) if row[7] else {},
            "created_at": row[8],
            "updated_at": row[9]
        }


def get_all_projects() -> List[Dict[str, Any]]:
    """Retrieve all tracked projects."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, client_objective, current_sprint, total_sprints, status, root_dir, updated_at FROM projects ORDER BY updated_at DESC;")
        rows = cursor.fetchall()
        return [{
            "id": r[0], "name": r[1], "client_objective": r[2], "current_sprint": r[3],
            "total_sprints": r[4], "status": r[5], "root_dir": r[6], "updated_at": r[7]
        } for r in rows]


def update_project_status(project_id: int, status: str, current_sprint: Optional[int] = None):
    """Update project status and optionally the active sprint number."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        cursor = conn.cursor()
        if current_sprint is not None:
            cursor.execute("""
                UPDATE projects SET status = ?, current_sprint = ?, updated_at = ? WHERE id = ?;
            """, (status, current_sprint, now, project_id))
        else:
            cursor.execute("""
                UPDATE projects SET status = ?, updated_at = ? WHERE id = ?;
            """, (status, now, project_id))
        conn.commit()


# ============================================================
# SPRINT & TASK CRUD
# ============================================================

def create_sprint_record(project_id: int, sprint_num: int, title: str, description: str) -> int:
    """Create a sprint stage record."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sprints (project_id, sprint_number, title, description, status)
            VALUES (?, ?, ?, ?, 'pending')
            ON CONFLICT(project_id, sprint_number) DO UPDATE SET
                title = excluded.title,
                description = excluded.description;
        """, (project_id, sprint_num, title, description))
        conn.commit()
        return cursor.lastrowid


def get_sprints_for_project(project_id: int) -> List[Dict[str, Any]]:
    """Get all sprints ordered by sprint number."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, sprint_number, title, description, status, deliverables_summary, review_notes, started_at, completed_at
            FROM sprints WHERE project_id = ? ORDER BY sprint_number ASC;
        """, (project_id,))
        return [{
            "id": r[0], "sprint_number": r[1], "title": r[2], "description": r[3],
            "status": r[4], "deliverables_summary": r[5], "review_notes": r[6],
            "started_at": r[7], "completed_at": r[8]
        } for r in cursor.fetchall()]


def update_sprint_status(project_id: int, sprint_num: int, status: str, summary: str = "", notes: str = ""):
    """Update sprint lifecycle state."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        cursor = conn.cursor()
        if status == 'active':
            cursor.execute("""
                UPDATE sprints SET status = ?, started_at = ? WHERE project_id = ? AND sprint_number = ?;
            """, (status, now, project_id, sprint_num))
        elif status == 'completed':
            cursor.execute("""
                UPDATE sprints SET status = ?, completed_at = ?, deliverables_summary = ?, review_notes = ?
                WHERE project_id = ? AND sprint_number = ?;
            """, (status, now, summary, notes, project_id, sprint_num))
        else:
            cursor.execute("""
                UPDATE sprints SET status = ?, deliverables_summary = ?, review_notes = ?
                WHERE project_id = ? AND sprint_number = ?;
            """, (status, summary, notes, project_id, sprint_num))
        conn.commit()


def save_artifact(project_id: int, sprint_num: int, artifact_type: str, relative_path: str, content: str):
    """Store generated project artifact (e.g. PRD, architecture, source files, tests)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO artifacts (project_id, sprint_number, artifact_type, relative_path, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (project_id, sprint_num, artifact_type, relative_path, content, now))
        conn.commit()


def get_artifacts_for_project(project_id: int, sprint_num: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve all artifacts for a project."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        if sprint_num is not None:
            cursor.execute("""
                SELECT id, sprint_number, artifact_type, relative_path, content, created_at
                FROM artifacts WHERE project_id = ? AND sprint_number = ? ORDER BY id ASC;
            """, (project_id, sprint_num))
        else:
            cursor.execute("""
                SELECT id, sprint_number, artifact_type, relative_path, content, created_at
                FROM artifacts WHERE project_id = ? ORDER BY sprint_number ASC, id ASC;
            """, (project_id,))
        return [{
            "id": r[0], "sprint_number": r[1], "artifact_type": r[2],
            "relative_path": r[3], "content": r[4], "created_at": r[5]
        } for r in cursor.fetchall()]


def record_standup_log(project_id: int, sprint_num: int, agent_name: str, yesterday: str, today: str, blockers: str = "None"):
    """Record daily standup milestone report for Morning Briefing."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO standup_logs (project_id, sprint_number, agent_name, yesterday_work, today_plan, blockers, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (project_id, sprint_num, agent_name, yesterday, today, blockers, now))
        conn.commit()


def get_latest_standup_for_active_projects() -> List[Dict[str, Any]]:
    """Retrieve the latest standup entry for currently active projects."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.name, s.sprint_number, s.title, l.agent_name, l.yesterday_work, l.today_plan, l.blockers, l.timestamp
            FROM standup_logs l
            JOIN projects p ON l.project_id = p.id
            JOIN sprints s ON (l.project_id = s.project_id AND l.sprint_number = s.sprint_number)
            WHERE p.status IN ('approved', 'in_progress', 'qa_review')
            ORDER BY l.id DESC
            LIMIT 3;
        """)
        rows = cursor.fetchall()
        return [{
            "project_name": r[0],
            "sprint_number": r[1],
            "sprint_title": r[2],
            "agent_name": r[3],
            "yesterday_work": r[4],
            "today_plan": r[5],
            "blockers": r[6],
            "timestamp": r[7]
        } for r in rows]


# Auto-initialize database on import
init_agency_db()

