"""
J.A.R.V.I.S. Client Intake & Requirements Discovery Engine
Acts as the Senior Business Analyst / Solutions Consultant:
1. Conducts client discovery interviews (platform, architecture, storage, scope).
2. Formulates formal Product Requirements Documents (PRD.md) with strict Acceptance Criteria.
3. Initializes the 5-Sprint Agile Roadmap for multi-day autonomous delivery.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from .db import (
    create_project_record,
    create_sprint_record,
    save_artifact,
    update_project_status,
    get_project_by_name,
)

PROJECTS_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "projects"
)


def detect_archetype(objective: str, platform_hint: str = "") -> str:
    """
    Detect the project archetype based on client objectives and platform hints.
    Supported: 'cli_tool', 'rest_api', 'gui_desktop', 'daemon_worker'.
    """
    combined = (objective + " " + platform_hint).lower()
    if any(k in combined for k in ["gui", "desktop", "customtkinter", "tkinter", "window", "frontend", "dashboard"]):
        return "gui_desktop"
    if any(k in combined for k in ["api", "rest", "fastapi", "flask", "endpoint", "backend", "web service", "http"]):
        return "rest_api"
    if any(k in combined for k in ["daemon", "service", "background", "watcher", "scheduler", "monitor", "pinger", "agent"]):
        return "daemon_worker"
    return "cli_tool"


def get_discovery_questions(project_name: str, brief: str) -> List[Dict[str, str]]:
    """
    Generate targeted discovery questions for the client based on initial brief.
    Returns list of discovery questionnaire items.
    """
    return [
        {
            "id": "platform",
            "question": f"What is the target platform for '{project_name}'? (Desktop GUI, Command-Line Tool, or Web API/Service)",
            "default": "Desktop GUI with CustomTkinter"
        },
        {
            "id": "core_features",
            "question": "What are the non-negotiable core features required for Version 1?",
            "default": "Automated data management, search/filtering, and persistent state."
        },
        {
            "id": "data_storage",
            "question": "What is the preferred data persistence strategy? (SQLite Database, JSON flat files, or CSV)",
            "default": "SQLite with thread-safe connection pooling"
        },
        {
            "id": "export_formats",
            "question": "Do you require data export or reporting? (CSV, JSON, PDF summaries, or None)",
            "default": "CSV and JSON export"
        },
        {
            "id": "constraints",
            "question": "Are there any specific constraints? (Zero cloud dependency / 100% offline, memory footprint limits)",
            "default": "100% offline, zero cloud API keys, clean modular architecture"
        }
    ]


def generate_prd_content(project_name: str, objective: str, answers: Dict[str, str]) -> str:
    """
    Compile a formal Product Requirements Document (PRD) with user stories,
    strict acceptance criteria, and a 5-Sprint delivery roadmap.
    """
    now = datetime.now().strftime("%B %d, %Y")
    clean_name = project_name.strip()
    platform = answers.get("platform", "Desktop Application")
    core_features = answers.get("core_features", "Core data processing and reporting")
    storage = answers.get("data_storage", "SQLite Relational Database")
    exports = answers.get("export_formats", "JSON & CSV")
    constraints = answers.get("constraints", "100% local and offline execution")

    prd_text = f"""# Product Requirements Document (PRD)
## Project: {clean_name}
**Version:** 1.0.0-PROD  
**Author:** J.A.R.V.I.S. Autonomous Engineering Agency  
**Client Sign-Off Date:** {now}  
**Status:** AWAITING CLIENT APPROVAL (Gate 1)

---

### 1. Executive Summary & Objective
{clean_name} is an enterprise-grade software solution designed to solve the following client directive:
> *"{objective.strip()}"*

The system will be architected according to strict industrial software standards: high modularity, comprehensive error isolation, defensive logging, and test-driven verification.

---

### 2. Technical Stack & Constraints
* **Target Interface / Platform:** {platform}
* **Persistence Layer:** {storage}
* **Export Protocols:** {exports}
* **Operational Constraints:** {constraints}
* **Language & Runtime:** Python 3.11+
* **Test Framework:** `unittest` / `pytest` with automated self-healing CI

---

### 3. Functional Requirements & User Stories

#### US-1: Core Domain Engine & Data Architecture
* **As a** Client / User  
* **I want to** reliably manage and persist project domain records  
* **So that** my data is consistently available without corruption across application restarts.
* **Acceptance Criteria:**
  - `AC-1.1`: Database tables and schemas must automatically initialize on first launch.
  - `AC-1.2`: All insert, read, update, and delete operations must have safe exception wrappers.
  - `AC-1.3`: Queries must execute in sub-50ms with zero memory leaks.

#### US-2: Primary Workflow & Business Logic
* **As a** Client / User  
* **I want to** execute: {core_features}  
* **So that** my operational objectives are fulfilled with maximum throughput.
* **Acceptance Criteria:**
  - `AC-2.1`: Input validation must reject malformed data with human-readable error messages.
  - `AC-2.2`: Business logic must be decoupled from UI/presentation components.
  - `AC-2.3`: Export routines for {exports} must generate valid output files.

#### US-3: Quality Assurance & Fault Tolerance
* **As a** System Auditor  
* **I want to** verify system integrity through automated unit test suites  
* **So that** zero unhandled crashes or regressions occur in production.
* **Acceptance Criteria:**
  - `AC-3.1`: Automated unit test coverage must verify every primary business rule.
  - `AC-3.2`: Edge cases (empty data, missing files, illegal characters) must fail gracefully.

---

### 4. 5-Sprint Multi-Day Delivery Roadmap

| Sprint | Phase | Milestone Objectives | Review Gate |
| :--- | :--- | :--- | :--- |
| **Sprint 1** | **Discovery & Architecture** | PRD sign-off, system architecture (`ARCHITECTURE.md`), modular directory setup, data models. | Gate 1 (Client Sign-Off) |
| **Sprint 2** | **Data & Storage Layer** | Database schema, repository pattern, CRUD operations, mock fixture seeding. | Gate 2 (Data Review) |
| **Sprint 3** | **Business Logic Engine** | Core functional controllers, input validation, export pipelines. | Gate 3 (Logic Review) |
| **Sprint 4** | **Interface & Integration** | User interface (CLI / GUI / API), status telemetry, multi-component wiring. | Gate 4 (Integration Review) |
| **Sprint 5** | **Deep QA & Client Handover**| Unit test suite, edge case hardening, `README.md`, setup launcher, and UAT sign-off. | Gate 5 (Final Delivery) |

---
*Generated autonomously by J.A.R.V.I.S. Software Engineering Division.*
"""
    return prd_text


def initiate_client_project(project_name: str, objective: str, custom_answers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Initiate a new client project:
    1. Sets up the project directory in `projects/<ProjectName>/`.
    2. Compiles the official `PRD.md`.
    3. Records the project in the database.
    4. Initializes Sprint 1 to 5 records.
    Returns project summary dictionary.
    """
    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', project_name.strip().replace(" ", "_"))
    if not clean_name:
        clean_name = "Enterprise_Project"

    project_root = os.path.join(PROJECTS_BASE_DIR, clean_name)
    os.makedirs(project_root, exist_ok=True)
    os.makedirs(os.path.join(project_root, "src"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "tests"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "docs"), exist_ok=True)

    # Use default answers if client provided none
    answers = custom_answers or {}
    for q in get_discovery_questions(clean_name, objective):
        if q["id"] not in answers:
            answers[q["id"]] = q["default"]

    prd_content = generate_prd_content(clean_name, objective, answers)

    # Write PRD.md to disk
    prd_path = os.path.join(project_root, "docs", "PRD.md")
    with open(prd_path, "w", encoding="utf-8") as f:
        f.write(prd_content)

    # Also keep a root copy for easy viewing
    root_prd_path = os.path.join(project_root, "PRD.md")
    with open(root_prd_path, "w", encoding="utf-8") as f:
        f.write(prd_content)

    # Create in database
    archetype = detect_archetype(objective, answers.get("platform", ""))
    metadata = {
        "answers": answers,
        "archetype": archetype,
        "prd_path": prd_path,
        "created_timestamp": datetime.now().isoformat()
    }
    project_id = create_project_record(clean_name, objective, project_root, metadata)

    # Save PRD artifact
    save_artifact(project_id, 1, "prd", "docs/PRD.md", prd_content)

    # Initialize the 5 Sprints
    sprints_info = [
        (1, "Discovery & Architecture", "PRD approval, technical architecture design, folder scaffolding."),
        (2, "Data & Storage Layer", "Database schemas, repositories, and data access persistence."),
        (3, "Business Logic Engine", "Core domain controllers, validation, and processing logic."),
        (4, "Interface & Integration", "User-facing interface (GUI/CLI/API) and subsystem wiring."),
        (5, "Deep QA & Client Handover", "Automated test suites, edge case verification, documentation, and delivery.")
    ]
    for s_num, s_title, s_desc in sprints_info:
        create_sprint_record(project_id, s_num, s_title, s_desc)

    update_project_status(project_id, status="prd_ready", current_sprint=1)

    return {
        "project_id": project_id,
        "project_name": clean_name,
        "name": clean_name,
        "archetype": archetype,
        "root_dir": project_root,
        "project_path": project_root,
        "prd_path": prd_path,
        "status": "prd_ready",
        "current_sprint": 1,
        "total_sprints": 5,
        "prd_content": prd_content
    }

