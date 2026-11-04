"""
Stark Autonomous Engineering Agency - Standalone Test Runner
Executes an end-to-end multi-role sprint cycle (Architect, Developer, QA, DevOps)
for the sample project 'ServerPulse'.
"""

import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.agency import (
    initiate_client_project,
    approve_project_prd,
    advance_project_to_completion,
    get_morning_standup_report,
    get_all_projects,
)


def run_sample_project_test():
    project_name = "ServerPulse"
    objective = "Automated server health and ping latency monitor with threshold alerting and SQLite database."

    print("=" * 70)
    print("  J.A.R.V.I.S. AUTONOMOUS SOFTWARE ENGINEERING STUDIO - TEST RUNNER")
    print("=" * 70)

    # Stage 1: Client Discovery & PRD formulation
    print(f"\n[STAGE 1/4] Client Intake & PRD Formulation for '{project_name}'...")
    proj = initiate_client_project(project_name, objective)
    print(f"  > Project created: {proj['project_name']} (ID: {proj['project_id']})")
    print(f"  > Total Sprints Initialized: {proj['total_sprints']}")
    print(f"  > Specification: projects/{proj['project_name']}/PRD.md")

    # Stage 2: Human Sign-off Gate
    print(f"\n[STAGE 2/4] Client Review Gate: Approving PRD...")
    app_res = approve_project_prd(proj["project_name"])
    print(f"  > Sign-off status: {app_res.get('status')}")
    print(f"  > Message: {app_res.get('message')}")

    # Stage 3: Multi-Role Sprint Execution (Architect, Developer, QA, DevOps)
    print(f"\n[STAGE 3/4] Executing Agile Sprints 1 to 5...")
    print("  - Sprint 1: System Architecture & Data Schema (ArchitectAgent)")
    print("  - Sprint 2: Data Layer & SQLite Persistence (DeveloperAgent)")
    print("  - Sprint 3: Core Service & Business Logic (DeveloperAgent)")
    print("  - Sprint 4: Application Integration & CLI (DeveloperAgent)")
    print("  - Sprint 5: Automated QA Subprocess Tests & Packaging (QAAgent & DevOpsAgent)")

    start_time = time.time()
    results = advance_project_to_completion(proj["project_name"])
    duration = time.time() - start_time

    print(f"\n  > All Sprints Completed in {duration:.2f}s!")
    print(f"  > QA Test Verification: {results.get('qa_status', 'N/A')}")
    print(f"  > Deliverables Output: {results.get('project_path')}")

    # Stage 4: Morning Standup Briefing Sync
    print(f"\n[STAGE 4/4] Morning Standup Audio Report (Synced to J.A.R.V.I.S. Briefing):")
    standup = get_morning_standup_report()
    print(f"  \"{standup}\"")

    print("\n" + "=" * 70)
    print(f"  TEST COMPLETE! You can inspect and run the generated project:")
    print(f"    cd {results.get('project_path')}")
    print(f"    .\\run.bat")
    print("=" * 70)


if __name__ == "__main__":
    run_sample_project_test()
