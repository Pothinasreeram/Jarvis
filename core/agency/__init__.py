"""
J.A.R.V.I.S. Autonomous Engineering Agency Package
Exports client intake, multi-agent orchestrator, and database APIs.
"""

from .db import (
    init_agency_db,
    get_project_by_id,
    get_project_by_name,
    get_all_projects,
    get_sprints_for_project,
    get_artifacts_for_project,
    get_latest_standup_for_active_projects,
)
from .client_intake import (
    get_discovery_questions,
    generate_prd_content,
    initiate_client_project,
    detect_archetype,
)
from .orchestrator import (
    start_project_intake,
    approve_project_prd,
    execute_sprint_stage,
    advance_project_to_completion,
    get_morning_standup_report,
    get_project_summary,
    apply_change_request,
)

__all__ = [
    "init_agency_db",
    "get_project_by_id",
    "get_project_by_name",
    "get_all_projects",
    "get_sprints_for_project",
    "get_artifacts_for_project",
    "get_latest_standup_for_active_projects",
    "get_discovery_questions",
    "generate_prd_content",
    "initiate_client_project",
    "detect_archetype",
    "start_project_intake",
    "approve_project_prd",
    "execute_sprint_stage",
    "advance_project_to_completion",
    "get_morning_standup_report",
    "get_project_summary",
    "apply_change_request",
]

