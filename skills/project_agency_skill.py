"""
Stark Autonomous Engineering Agency Skill for J.A.R.V.I.S.
Handles voice and console directives for multi-day agile project management:
- "Jarvis, assemble team to build <project>"
- "Jarvis, start project <name>"
- "Jarvis, project standup"
- "Jarvis, project status"
- "Jarvis, approve project" / "approve PRD"
- "Jarvis, run next sprint"
- "Jarvis, list projects"
"""

import re
from typing import Dict, Any, List

from core.agency import (
    start_project_intake,
    approve_project_prd,
    execute_sprint_stage,
    advance_project_to_completion,
    get_morning_standup_report,
    get_project_summary,
    get_all_projects,
)

skill = {
    "name": "Autonomous Project Studio",
    "priority": 14,
}

TRIGGER_KEYWORDS = [
    "assemble team",
    "assemble the team",
    "start project",
    "new project",
    "create project",
    "project standup",
    "engineering standup",
    "project status",
    "approve prd",
    "approve project",
    "run sprint",
    "next sprint",
    "run next sprint",
    "list projects",
    "show projects",
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if "project" in cmd and any(w in cmd for w in ["assemble", "sprint", "standup", "agency", "prd"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # 1. Standup report
    if any(k in cmd for k in ["standup", "daily standup", "engineering update"]):
        report = get_morning_standup_report()
        if report:
            return report
        return "All engineering project queues are currently clear, Sir. No active sprint standups recorded."

    # 2. List projects
    if any(k in cmd for k in ["list projects", "show projects", "what projects"]):
        projects = get_all_projects()
        if not projects:
            return "No projects currently tracked in the engineering database, Sir."
        lines = []
        for p in projects[:5]:
            p_name = p["name"].replace("_", " ")
            status = p["status"].replace("_", " ").title()
            sprint = p["current_sprint"]
            total = p["total_sprints"]
            lines.append(f"{p_name}: Sprint {sprint}/{total} ({status})")
        return "Current Engineering Projects:\n" + "\n".join(f"- {l}" for l in lines)

    # 3. Project status
    if "project status" in cmd or "status of project" in cmd:
        # Check if project name specified
        projects = get_all_projects()
        if not projects:
            return "No projects currently tracked in the database, Sir."

        # If user named a specific project
        target_proj = None
        for p in projects:
            if p["name"].lower() in cmd:
                target_proj = p
                break
        if not target_proj:
            target_proj = projects[0]  # default to most recent

        summary = get_project_summary(target_proj["id"])
        s_num = summary["current_sprint"]
        status = summary["status"].replace("_", " ").title()
        p_name = summary["name"].replace("_", " ")
        return f"Project {p_name} is currently in {status} state, at Sprint {s_num} of 5. Deliverables saved in projects/{summary['name']}."

    # 4. Approve PRD / Project
    if any(k in cmd for k in ["approve prd", "approve project", "sign off prd", "signoff prd"]):
        projects = get_all_projects()
        if not projects:
            return "No projects awaiting approval, Sir."
        target_proj = projects[0]
        res = approve_project_prd(target_proj["id"])
        if res.get("success"):
            return f"Client sign-off confirmed, Sir. PRD for {target_proj['name'].replace('_', ' ')} is approved. Sprint 1 architecture has been initiated."
        return res.get("message", "Unable to approve project.")

    # 5. Run next sprint
    if any(k in cmd for k in ["next sprint", "run sprint", "run next sprint", "advance sprint"]):
        projects = get_all_projects()
        if not projects:
            return "No active projects found to advance, Sir."
        target_proj = projects[0]
        res = execute_sprint_stage(target_proj["id"])
        if res.get("success"):
            return f"Sprint {res['sprint_number']} execution completed for {target_proj['name'].replace('_', ' ')}. {res.get('summary', '')}"
        return res.get("message", "Unable to advance sprint.")

    # 6. Start new project / Assemble team
    patterns = [
        r"(?:jarvis\s+)?(?:please\s+)?(?:assemble\s+team\s+to\s+build|assemble\s+the\s+team\s+to\s+build|start\s+project|new\s+project|create\s+project)\s+(.+)",
    ]
    for p in patterns:
        m = re.match(p, cmd)
        if m:
            raw_target = m.group(1).strip()
            # If target has "for" or description
            p_name = raw_target.split(" to ")[0].split(" that ")[0].split(" for ")[0].strip()
            objective = raw_target
            proj = start_project_intake(p_name, objective)
            clean_display_name = proj["name"].replace("_", " ")
            return (
                f"Client intake completed for Project {clean_display_name}, Sir. "
                f"I have formulated the official Product Requirements Document and 5-Sprint roadmap in projects/{proj['name']}/PRD.md. "
                f"Say 'approve PRD' to sign off and begin technical architecture."
            )

    return "Project studio command acknowledged, Sir."

