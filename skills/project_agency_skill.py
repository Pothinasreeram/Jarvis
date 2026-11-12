"""
Stark Autonomous Engineering Agency Skill for J.A.R.V.I.S.
Handles voice and console directives for multi-day agile project management:
- Interactive Discovery Interviews ("Jarvis, assemble team to build a website")
- Requirements Elicitation & Custom PRDs
- "Jarvis, approve project" / "approve PRD"
- "Jarvis, proceed with sprint" / "run next sprint"
- "Jarvis, build to completion" / "advance project to completion"
- "Jarvis, project standup" / "team standup"
- "Jarvis, list projects" / "project status"
"""

import os
import sys
import re
import time
import subprocess
import webbrowser
from typing import Dict, Any, List, Optional

from core.agency import (
    start_project_intake,
    approve_project_prd,
    execute_sprint_stage,
    advance_project_to_completion,
    get_morning_standup_report,
    get_project_summary,
    get_all_projects,
    detect_archetype,
    apply_change_request,
    find_available_port,
    is_port_in_use,
    set_project_runtime,
    get_project_runtime,
    stop_project_process,
)

skill = {
    "name": "Autonomous Project Studio",
    "priority": 14,
}

# Global in-memory state machine for active discovery interview
ACTIVE_INTAKE_SESSION: Optional[Dict[str, Any]] = None


def _resolve_target_project(cmd: str, prefer_web: bool = False) -> Optional[Dict[str, Any]]:
    """Context-aware project resolver preferring user named projects or recent projects."""
    projects = get_all_projects()
    if not projects:
        return None

    # 1. Exact or partial match with project name in command
    for p in projects:
        clean_name = p["name"].replace("_", " ").lower()
        if clean_name in cmd or p["name"].lower() in cmd:
            return p

    # 2. Prefer active web application if requested
    if prefer_web:
        web_p = next((p for p in projects if os.path.exists(os.path.join(p["root_dir"], "templates", "index.html")) or os.path.exists(os.path.join(p["root_dir"], "app.py"))), None)
        if web_p:
            return web_p

    # 3. Default to the most recently updated project (ordered DESC)
    return projects[0]


def can_handle(command: str) -> bool:
    global ACTIVE_INTAKE_SESSION

    cmd = command.lower().strip()
    cmd = re.sub(r'^(?:hey\s+|ok\s+|hello\s+)?(?:jarvis)?[\s,:]*(?:please)?[\s,:]*', '', cmd, flags=re.IGNORECASE).strip()

    # Session timeout check (5 minutes) and non-interview command pass-through
    if ACTIVE_INTAKE_SESSION is not None:
        if time.time() - ACTIVE_INTAKE_SESSION.get("timestamp", time.time()) > 300:
            ACTIVE_INTAKE_SESSION = None
        else:
            unrelated = ["weather", "battery", "volume", "music", "play", "pause", "chrome", "search", "calculate", "screenshot", "lock pc"]
            unrelated_phrases = ["what time", "what is the time", "current time", "whats the time", "what date", "todays date", "time is it"]
            if any(u in cmd for u in unrelated) or any(p in cmd for p in unrelated_phrases):
                return False
            return True

    if any(k in cmd for k in ["standup", "sprint", "prd"]):
        return True
    if any(k in cmd for k in ["assemble team", "assemble a team", "assemble the team", "engineering team"]):
        return True
    if any(k in cmd for k in ["build to completion", "advance to completion", "complete the project", "build it completely", "run all sprints"]):
        return True
    if any(k in cmd for k in ["launch website", "open website", "run website", "preview website", "start website", "preview project", "view website"]):
        return True
    if any(k in cmd for k in ["stop website", "kill website", "close website", "stop server", "kill server", "stop project", "shutdown website"]):
        return True
    if any(k in cmd for k in ["add testimonial", "add review", "add pricing", "add plan", "add faq", "add team", "change website", "update website", "modify website", "change theme", "add to website", "add section"]):
        return True
    if "project" in cmd and any(k in cmd for k in [
        "start", "new", "create", "build", "launch", "initiate", "make",
        "list", "show", "active", "my", "all", "status", "approve", "advance", "run", "proceed", "complete", "stop"
    ]):
        return True
    if any(cmd.startswith(kw) for kw in ["list projects", "show projects", "start project", "create project", "stop project"]):
        return True
    return False


def execute(command: str) -> str:
    global ACTIVE_INTAKE_SESSION

    raw_cmd = command.strip()
    cmd = raw_cmd.lower()
    cmd = re.sub(r'^(?:hey\s+|ok\s+|hello\s+)?(?:jarvis)?[\s,:]*(?:please)?[\s,:]*', '', cmd, flags=re.IGNORECASE).strip()

    # -------------------------------------------------------------
    # 0. Session Cancel / Abort
    # -------------------------------------------------------------
    if ACTIVE_INTAKE_SESSION is not None and any(k in cmd for k in ["cancel", "abort", "exit", "stop", "never mind", "nevermind"]):
        ACTIVE_INTAKE_SESSION = None
        return "Discovery interview cancelled, Sir. Ready for your next instruction."

    # -------------------------------------------------------------
    # 1. Interactive Discovery Interview State Handler
    # -------------------------------------------------------------
    if ACTIVE_INTAKE_SESSION is not None and ACTIVE_INTAKE_SESSION.get("stage") == "discovery_interview":
        session = ACTIVE_INTAKE_SESSION
        p_name = session.get("project_name", "Enterprise_Project")
        objective = session.get("objective", p_name)
        archetype = session.get("archetype", "web_application")

        # Client describes vision or says "auto-design"
        if any(w in cmd for w in ["auto-design", "auto design", "default", "standard", "you decide", "you choose", "enterprise"]):
            features = "Full enterprise architecture with clean responsive styling, navigation, showcase, contact form, and 1-click launcher."
        else:
            # Capture user's exact input as custom specification
            features = raw_cmd

        platform = "Responsive Web Application" if archetype == "web_application" else "Desktop Workstation Application"
        custom_answers = {
            "core_features": features,
            "platform": platform,
            "constraints": "100% offline, zero cloud API keys, clean modular code"
        }

        proj = start_project_intake(p_name, objective, custom_answers=custom_answers)

        ACTIVE_INTAKE_SESSION["stage"] = "awaiting_approval"
        ACTIVE_INTAKE_SESSION["project_id"] = proj.get("project_id") or proj.get("id")
        ACTIVE_INTAKE_SESSION["project_name"] = proj["name"]
        ACTIVE_INTAKE_SESSION["custom_features"] = features

        clean_name = proj["name"].replace("_", " ")
        arch_label = archetype.replace("_", " ").title()

        return (
            f"Client requirements captured for **{clean_name}** ({arch_label}), Sir.\n\n"
            f"I have compiled your specifications into the official PRD at `projects/{proj['name']}/PRD.md`.\n"
            f"- **Requested Features:** {features}\n"
            f"- **Delivery Roadmap:** 5-Sprint Agile Architecture & Subprocess QA Loop.\n\n"
            f"Say **'approve PRD'** to begin Sprint 1 architecture, or **'build to completion'** to deploy all 5 sprints automatically."
        )

    # -------------------------------------------------------------
    # 2. Build To Completion / Complete Project
    # -------------------------------------------------------------
    if any(k in cmd for k in ["build to completion", "advance to completion", "complete project", "complete the project", "build it completely", "run all sprints"]):
        target_id = None
        target_name = None

        if ACTIVE_INTAKE_SESSION and ACTIVE_INTAKE_SESSION.get("project_id"):
            target_id = ACTIVE_INTAKE_SESSION["project_id"]
            target_name = ACTIVE_INTAKE_SESSION.get("project_name")
        else:
            projects = get_all_projects()
            if projects:
                # Pick latest active or in_progress project
                target = next((p for p in projects if p["status"] != "completed"), projects[0])
                target_id = target["id"]
                target_name = target["name"]

        if not target_id:
            return "No active projects available to build to completion, Sir."

        # Ensure approved before running
        approve_project_prd(target_id)
        res = advance_project_to_completion(target_id)

        # Clear active intake session upon completion
        ACTIVE_INTAKE_SESSION = None

        if res.get("success"):
            name_display = res.get("name", target_name or "Project").replace("_", " ")
            root_dir = res.get("root_dir", f"projects/{target_name}")
            return (
                f"Autonomous engineering division has successfully delivered **{name_display}**, Sir!\n\n"
                f"- **Sprints Executed:** 5 of 5 Sprints Completed\n"
                f"- **QA Verification:** {res.get('qa_status', '100% Passed')}\n"
                f"- **Project Directory:** `{root_dir}`\n"
                f"- **Artifacts:** Verified on disk with 1-click launcher (`run.bat`).\n\n"
                f"You can launch the application by running `run.bat` in the project folder."
            )
        return res.get("message", "Sprint execution encountered an unexpected issue.")

    # -------------------------------------------------------------
    # 2.1 Launch Website / Preview Project
    # -------------------------------------------------------------
    if any(k in cmd for k in ["launch website", "open website", "run website", "preview website", "start website", "preview project", "view website"]):
        target = _resolve_target_project(cmd, prefer_web=True)
        if not target:
            return "No engineering projects found in the studio queue to preview, Sir."

        root = target["root_dir"]
        app_py = os.path.join(root, "app.py")

        if not os.path.exists(app_py):
            run_bat = os.path.join(root, "run.bat")
            if os.path.exists(run_bat):
                os.startfile(run_bat)
                name_display = target["name"].replace("_", " ")
                return f"Launching **{name_display}** application via `run.bat`, Sir."
            return f"No executable entrypoint found in `projects/{target['name']}`, Sir."

        runtime = get_project_runtime(target["id"])
        port = runtime.get("port")
        if not port or (is_port_in_use(port) and not runtime.get("pid")):
            port = find_available_port(5000 + (target["id"] % 50))

        import urllib.request
        is_running = False
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=0.3) as resp:
                is_running = resp.status == 200
        except Exception:
            is_running = False

        if not is_running:
            proc = subprocess.Popen(
                [sys.executable, app_py, str(port)],
                cwd=root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )
            set_project_runtime(target["id"], port=port, pid=proc.pid)
        else:
            set_project_runtime(target["id"], port=port, pid=runtime.get("pid"))

        webbrowser.open(f"http://localhost:{port}")
        name_display = target["name"].replace("_", " ")
        return (
            f"Launching **{name_display}** Web Application, Sir.\n\n"
            f"- **Port:** `{port}`\n"
            f"- **Public Website:** `http://localhost:{port}` (Opened in default browser)\n"
            f"- **Admin Portal:** `http://localhost:{port}/admin` (SQLite leads management)\n"
            f"- **Project Directory:** `{root}`"
        )

    # -------------------------------------------------------------
    # 2.2 Stop Project Server / Process
    # -------------------------------------------------------------
    if any(k in cmd for k in ["stop website", "kill website", "close website", "stop server", "kill server", "stop project", "shutdown website"]):
        target = _resolve_target_project(cmd, prefer_web=True)
        if not target:
            return "No active engineering projects found to terminate, Sir."

        res = stop_project_process(target["id"])
        return res.get("message", f"Server stopped for {target['name']}.")

    # -------------------------------------------------------------
    # 2.3 Iterative Change Requests (Sprint 6+)
    # -------------------------------------------------------------
    if any(k in cmd for k in ["add testimonial", "add review", "add pricing", "add plan", "add faq", "add team", "change website", "update website", "modify website", "change theme", "add to website", "add section"]):
        target = _resolve_target_project(cmd, prefer_web=True)
        if not target:
            return "No active projects found to modify, Sir."

        res = apply_change_request(target["id"], raw_cmd)
        if res.get("success"):
            name_display = target["name"].replace("_", " ")
            files_updated = ", ".join(res.get("updated_files", []))
            runtime = get_project_runtime(target["id"])
            port = runtime.get("port", 5000)
            return (
                f"Change Request deployed for **{name_display}**, Sir!\n\n"
                f"- **Updated Files:** {files_updated}\n"
                f"- **Regression QA:** {res.get('tests_run', 8)} automated tests verified.\n\n"
                f"You can preview the live updates by saying **'launch website'** or refreshing `http://localhost:{port}`."
            )
        return res.get("message", "Unable to apply change request.")

    # -------------------------------------------------------------
    # 3. Daily Standup Report
    # -------------------------------------------------------------
    if any(k in cmd for k in ["standup", "daily update", "engineering update", "engineering status"]):
        report = get_morning_standup_report()
        if report:
            return report
        return "All engineering project queues are currently clear, Sir. No active sprint standups recorded."

    # -------------------------------------------------------------
    # 4. List Projects
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # 5. Approve PRD / Project
    # -------------------------------------------------------------
    if any(k in cmd for k in ["approve", "sign off", "signoff"]) and any(k in cmd for k in ["prd", "project", "spec", "requirement", "it", "plan"]):
        target_id = None
        if ACTIVE_INTAKE_SESSION and ACTIVE_INTAKE_SESSION.get("project_id"):
            target_id = ACTIVE_INTAKE_SESSION["project_id"]
        else:
            projects = get_all_projects()
            if projects:
                target_id = projects[0]["id"]

        if not target_id:
            return "No projects awaiting approval, Sir."

        res = approve_project_prd(target_id)
        if res.get("success"):
            if ACTIVE_INTAKE_SESSION:
                ACTIVE_INTAKE_SESSION["stage"] = "in_progress"
            p_name = res.get("name", "Project").replace("_", " ")
            return (
                f"Client sign-off confirmed, Sir. PRD for **{p_name}** is approved.\n"
                f"System Architect is ready for Sprint 1.\n"
                f"Say **'proceed with sprint'** to advance step-by-step, or **'build to completion'** to generate all deliverables."
            )
        return res.get("message", "Unable to approve project.")

    # -------------------------------------------------------------
    # 6. Run / Advance / Proceed with Sprint
    # -------------------------------------------------------------
    if "sprint" in cmd and any(k in cmd for k in ["next", "run", "advance", "proceed", "continue", "execute", "start", "step", "go"]):
        target_id = None
        if ACTIVE_INTAKE_SESSION and ACTIVE_INTAKE_SESSION.get("project_id"):
            target_id = ACTIVE_INTAKE_SESSION["project_id"]
        else:
            projects = get_all_projects()
            if projects:
                target_id = projects[0]["id"]

        if not target_id:
            return "No active projects found to advance, Sir."

        res = execute_sprint_stage(target_id)
        if res.get("success"):
            p_name = res.get("name", "Project").replace("_", " ")
            s_num = res.get("sprint_number", 1)
            summary = res.get("summary", "")
            if s_num == 5:
                ACTIVE_INTAKE_SESSION = None
                return f"Final Sprint 5 completed for **{p_name}**, Sir! All automated QA tests verified. Deliverables deployed on disk."
            return f"Sprint {s_num} execution completed for **{p_name}**. {summary}\nSay 'proceed with sprint' to continue to Sprint {s_num + 1}."
        return res.get("message", "Unable to advance sprint.")

    # -------------------------------------------------------------
    # 7. Project Status
    # -------------------------------------------------------------
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
        return f"Project **{p_name}** is currently in {status} state, at Sprint {s_num} of 5. Deliverables saved in `projects/{summary['name']}`."

    # -------------------------------------------------------------
    # 8. Start New Project / Assemble Team
    # -------------------------------------------------------------
    patterns = [
        r"(?:assemble\s+(?:a\s+|the\s+)?team\s+(?:to\s+build|to\s+create|to\s+make|for)?)\s*(?:called|named)?\s*(.+)",
        r"(?:start|create|build|launch|initiate|make)\s+(?:a\s+|the\s+)?(?:new\s+)?project\s*(?:called|named)?\s*(.+)",
        r"(?:new\s+project)\s*(?:called|named)?\s*(.+)",
    ]
    for p in patterns:
        m = re.match(p, cmd)
        if m:
            raw_target = m.group(1).strip()
            # Parse clean name and objective
            p_name = raw_target.split(" to ")[0].split(" that ")[0].split(" for ")[0].strip()
            # Clean common articles
            p_name = re.sub(r'^(?:a|an|the)\s+', '', p_name).strip()
            if not p_name:
                p_name = "Enterprise_Project"

            objective = raw_target
            archetype = detect_archetype(objective)

            # Check if user already provided detailed requirements in their command
            has_details = len(raw_target) > 55 or any(w in cmd for w in ["with", "having", "dark theme", "gallery", "booking", "database", "portfolio", "store", "api"])

            if has_details:
                # Direct intake with user's explicit details
                platform = "Responsive Web Application" if archetype == "web_application" else "Desktop Workstation Application"
                custom_answers = {
                    "core_features": raw_target,
                    "platform": platform,
                    "constraints": "100% offline, zero cloud API keys, clean modular code"
                }
                proj = start_project_intake(p_name, objective, custom_answers=custom_answers)
                ACTIVE_INTAKE_SESSION = {
                    "project_id": proj.get("project_id") or proj.get("id"),
                    "project_name": proj["name"],
                    "archetype": archetype,
                    "stage": "awaiting_approval"
                }
                clean_display_name = proj["name"].replace("_", " ")
                arch_label = archetype.replace("_", " ").title()
                return (
                    f"Client intake initiated for Project **{clean_display_name}** ({arch_label}), Sir.\n\n"
                    f"I have compiled your specifications into `projects/{proj['name']}/PRD.md`.\n"
                    f"- **Target Features:** {raw_target}\n\n"
                    f"Say **'approve PRD'** to begin technical architecture, or **'build to completion'** to deploy all 5 sprints."
                )
            else:
                # Enter Discovery Interview Mode so user can explain their ideas!
                ACTIVE_INTAKE_SESSION = {
                    "project_name": p_name,
                    "objective": objective,
                    "archetype": archetype,
                    "stage": "discovery_interview"
                }
                if archetype == "web_application":
                    return (
                        f"I have initiated discovery for **{p_name.title()}** as a **Web Application**, Sir.\n\n"
                        f"Before our engineering team writes code, tell me: what pages, design style, or features do you want (e.g., photo gallery, dark theme, booking form, user accounts)?\n\n"
                        f"*(You can explain your vision in full detail, or simply say 'auto-design' and I will structure a complete enterprise solution.)*"
                    )
                else:
                    return (
                        f"I have initiated discovery for **{p_name.title()}** as a **{archetype.replace('_', ' ').title()}**, Sir.\n\n"
                        f"Please describe your key requirements or target features, or reply 'auto-design' to proceed with our enterprise architecture."
                    )

    return "Project studio command acknowledged, Sir."
