"""
Stark Autonomous Engineering Agency Skill for J.A.R.V.I.S.
Handles voice and console directives for multi-day agile project management:
- "Jarvis, assemble team to build <project>"
- "Jarvis, start project <name>"
- "Jarvis, project standup" / "team standup"
- "Jarvis, project status"
- "Jarvis, approve project" / "approve PRD"
- "Jarvis, proceed with sprint" / "run next sprint"
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


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    cmd = re.sub(r'^(?:hey\s+|ok\s+|hello\s+)?(?:jarvis\s+)?(?:please\s+)?', '', cmd).strip()

    if any(k in cmd for k in ["standup", "sprint", "prd"]):
        return True
    if any(k in cmd for k in ["assemble team", "assemble a team", "assemble the team", "engineering team"]):
        return True
    if "project" in cmd and any(k in cmd for k in [
        "start", "new", "create", "build", "launch", "initiate", "make",
        "list", "show", "active", "my", "all", "status", "approve", "advance", "run", "proceed"
    ]):
        return True
    if any(cmd.startswith(kw) for kw in ["list projects", "show projects", "start project", "create project"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()
    cmd = re.sub(r'^(?:hey\s+|ok\s+|hello\s+)?(?:jarvis\s+)?(?:please\s+)?', '', cmd).strip()

    # 1. Standup report
    if any(k in cmd for k in ["standup", "daily update", "engineering update", "engineering status"]):
        report = get_morning_standup_report()
        if report:
            return report
        return "All engineering project queues are currently clear, Sir. No active sprint standups recorded."

    # 2. List projects
    if any(k in cmd for k in ["list project", "show project", "my project", "all project", "what project", "active project"]):
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

    # 3. Approve PRD / Project
    if any(k in cmd for k in ["approve", "sign off", "signoff"]) and any(k in cmd for k in ["prd", "project", "spec", "requirement"]):
        projects = get_all_projects()
        if not projects:
            return "No projects awaiting approval, Sir."
        target_proj = projects[0]
        res = approve_project_prd(target_proj["id"])
        if res.get("success"):
            return f"Client sign-off confirmed, Sir. PRD for {target_proj['name'].replace('_', ' ')} is approved. Sprint 1 architecture has been initiated."
        return res.get("message", "Unable to approve project.")

    # 4. Run / Advance / Proceed with Sprint
    if "sprint" in cmd and any(k in cmd for k in ["next", "run", "advance", "proceed", "continue", "execute", "start", "step", "go"]):
        projects = get_all_projects()
        if not projects:
            return "No active projects found to advance, Sir."
        target_proj = projects[0]
        res = execute_sprint_stage(target_proj["id"])
        if res.get("success"):
            return f"Sprint {res['sprint_number']} execution completed for {target_proj['name'].replace('_', ' ')}. {res.get('summary', '')}"
        return res.get("message", "Unable to advance sprint.")

    # 5. Project status
    if "status" in cmd and "project" in cmd:
        projects = get_all_projects()
        if not projects:
            return "No projects currently tracked in the database, Sir."

        target_proj = None
        for p in projects:
            if p["name"].lower() in cmd:
                target_proj = p
                break
        if not target_proj:
            target_proj = projects[0]

        summary = get_project_summary(target_proj["id"])
        s_num = summary["current_sprint"]
        status = summary["status"].replace("_", " ").title()
        p_name = summary["name"].replace("_", " ")
        return f"Project {p_name} is currently in {status} state, at Sprint {s_num} of 5. Deliverables saved in projects/{summary['name']}."

    # 6. Start new project / Assemble team
    patterns = [
        r"(?:assemble\s+(?:a\s+|the\s+)?team\s+(?:to\s+build|to\s+create|to\s+make|for)?)\s*(?:called|named)?\s*(.+)",
        r"(?:start|create|build|launch|initiate|make)\s+(?:a\s+|the\s+)?(?:new\s+)?project\s*(?:called|named)?\s*(.+)",
        r"(?:new\s+project)\s*(?:called|named)?\s*(.+)",
    ]
    for p in patterns:
        m = re.match(p, cmd)
        if m:
            raw_target = m.group(1).strip()
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
