"""
Comprehensive Automated Unit Tests for J.A.R.V.I.S. Autonomous Engineering Agency
Verifies:
1. Agency Database schema & CRUD (projects, sprints, artifacts, standup logs).
2. Client Intake, discovery questionnaire & PRD generation with Acceptance Criteria.
3. Architect, Developer, QA, and DevOps agent generation.
4. Real subprocess test execution and QA pass auditing.
5. End-to-end multi-sprint lifecycle and Morning Briefing standup reporting.
6. Skill command parsing and keyword routing.
"""

import unittest
import os
import shutil
import tempfile
import time

from core.agency.db import (
    init_agency_db,
    create_project_record,
    get_project_by_id,
    get_project_by_name,
    get_all_projects,
    update_project_status,
    create_sprint_record,
    get_sprints_for_project,
    save_artifact,
    get_artifacts_for_project,
    record_standup_log,
    get_latest_standup_for_active_projects,
    find_available_port,
    set_project_runtime,
    get_project_runtime,
    stop_project_process,
)
from core.agency.client_intake import (
    get_discovery_questions,
    generate_prd_content,
    initiate_client_project,
)
from core.agency.agents import (
    ArchitectAgent,
    DeveloperAgent,
    QAAgent,
    DevOpsAgent,
)
from core.agency.orchestrator import (
    start_project_intake,
    approve_project_prd,
    execute_sprint_stage,
    advance_project_to_completion,
    apply_change_request,
    get_morning_standup_report,
    get_project_summary,
)
import skills.project_agency_skill as agency_skill


class TestAgencyDatabase(unittest.TestCase):
    """Test SQLite persistence layer for projects and sprints."""

    def test_database_initialization(self):
        init_agency_db()
        p_name = f"Test_Project_Alpha_{int(time.time() * 1000)}"
        p_id = create_project_record(p_name, "Automated system monitoring", "C:\\DummyPath")
        self.assertGreater(p_id, 0)

        proj = get_project_by_id(p_id)
        self.assertIsNotNone(proj)
        self.assertEqual(proj["name"], p_name)

        # Test sprint creation
        s_id = create_sprint_record(p_id, 1, "Discovery", "Initial PRD review")
        self.assertGreater(s_id, 0)

        sprints = get_sprints_for_project(p_id)
        self.assertEqual(len(sprints), 1)
        self.assertEqual(sprints[0]["title"], "Discovery")

        # Test artifact saving
        save_artifact(p_id, 1, "prd", "docs/PRD.md", "# Sample PRD")
        artifacts = get_artifacts_for_project(p_id)
        self.assertEqual(len(artifacts), 1)

        # Test standup log
        record_standup_log(p_id, 1, "Architect", "Designed blueprint", "Proceed to data layer")
        standups = get_latest_standup_for_active_projects()
        self.assertTrue(isinstance(standups, list))

    def test_process_lifecycle_and_ports(self):
        p_name = f"Test_Runtime_{int(time.time() * 1000)}"
        p_id = create_project_record(p_name, "Runtime management test", "C:\\DummyPath")
        port = find_available_port(5000)
        self.assertGreaterEqual(port, 5000)

        # Set runtime with a real temporary subprocess
        import subprocess, sys
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            set_project_runtime(p_id, port=port, pid=proc.pid)
            runtime = get_project_runtime(p_id)
            self.assertEqual(runtime.get("port"), port)
            self.assertEqual(runtime.get("pid"), proc.pid)
            self.assertEqual(runtime.get("status"), "running")

            # Stop process
            res = stop_project_process(p_id)
            self.assertTrue(res["success"])
            runtime_after = get_project_runtime(p_id)
            self.assertIsNone(runtime_after.get("pid"))
        finally:
            if proc.poll() is None:
                proc.kill()


class TestClientIntakeAndPRD(unittest.TestCase):
    """Test Client Discovery questions and PRD generation."""

    def test_discovery_questions(self):
        qs = get_discovery_questions("InventoryManager", "Track stock levels")
        self.assertGreaterEqual(len(qs), 4)
        ids = [q["id"] for q in qs]
        self.assertIn("platform", ids)
        self.assertIn("data_storage", ids)

    def test_prd_compilation_contains_acceptance_criteria(self):
        answers = {
            "platform": "Desktop GUI",
            "core_features": "Fast stock lookup",
            "data_storage": "SQLite",
            "export_formats": "CSV",
            "constraints": "100% offline"
        }
        prd = generate_prd_content("StockMaster", "Automated inventory tracking", answers)
        self.assertIn("Product Requirements Document", prd)
        self.assertIn("Acceptance Criteria", prd)
        self.assertIn("5-Sprint Multi-Day Delivery Roadmap", prd)
        self.assertIn("StockMaster", prd)


class TestAgentExecution(unittest.TestCase):
    """Test code generation and QA subprocess execution."""

    def setUp(self):
        self.temp_proj = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_proj, "src"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_proj, "tests"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_proj, ignore_errors=True)

    def test_architect_generation(self):
        arch = ArchitectAgent.design_architecture("ExpenseTracker", "Track expenses", "# PRD Mock")
        self.assertIn("Technical Architecture Document", arch)
        self.assertIn("Layered Architecture", arch)

    def test_developer_and_qa_subprocess_execution(self):
        # 1. Generate code files in temporary sandbox
        models_code = DeveloperAgent.generate_models_code("ExpenseTracker")
        db_code = DeveloperAgent.generate_database_code("ExpenseTracker")
        service_code = DeveloperAgent.generate_service_code("ExpenseTracker")
        test_code = QAAgent.generate_test_suite_code("ExpenseTracker")

        with open(os.path.join(self.temp_proj, "src", "models.py"), "w", encoding="utf-8") as f:
            f.write(models_code)
        with open(os.path.join(self.temp_proj, "src", "database.py"), "w", encoding="utf-8") as f:
            f.write(db_code)
        with open(os.path.join(self.temp_proj, "src", "service.py"), "w", encoding="utf-8") as f:
            f.write(service_code)
        with open(os.path.join(self.temp_proj, "tests", "test_core.py"), "w", encoding="utf-8") as f:
            f.write(test_code)

        # 2. Run QA execution in subprocess
        qa_result = QAAgent.execute_test_suite(self.temp_proj)
        self.assertTrue(qa_result["success"], f"QA test suite failed: {qa_result['output']}")
        self.assertGreaterEqual(qa_result["tests_run"], 4)

    def test_archetype_detection(self):
        from core.agency.client_intake import detect_archetype
        self.assertEqual(detect_archetype("Build a desktop GUI dashboard"), "gui_desktop")
        self.assertEqual(detect_archetype("Create a REST API for banking"), "rest_api")
        self.assertEqual(detect_archetype("A background daemon service"), "daemon_worker")
        self.assertEqual(detect_archetype("CLI tool to parse csv"), "cli_tool")
        self.assertEqual(detect_archetype("Build a modern website for photography"), "web_application")
        self.assertEqual(detect_archetype("Create a web app landing page with HTML and CSS"), "web_application")

    def test_self_healing_qa_loop(self):
        models_code = DeveloperAgent.generate_models_code("SelfHealingTest")
        db_code = DeveloperAgent.generate_database_code("SelfHealingTest")
        service_code = DeveloperAgent.generate_service_code("SelfHealingTest")
        test_code = QAAgent.generate_test_suite_code("SelfHealingTest")

        with open(os.path.join(self.temp_proj, "src", "models.py"), "w", encoding="utf-8") as f:
            f.write(models_code)
        with open(os.path.join(self.temp_proj, "src", "database.py"), "w", encoding="utf-8") as f:
            f.write(db_code)
        with open(os.path.join(self.temp_proj, "src", "service.py"), "w", encoding="utf-8") as f:
            f.write(service_code)
        with open(os.path.join(self.temp_proj, "tests", "test_core.py"), "w", encoding="utf-8") as f:
            f.write(test_code)

        result = QAAgent.run_tests_with_healing(self.temp_proj, max_attempts=2)
        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["tests_run"], 4)


class TestOrchestratorLifecycle(unittest.TestCase):
    """Test full multi-sprint lifecycle and Gate sign-off."""

    def test_end_to_end_project_workflow(self):
        # 1. Start intake
        p_name = f"DocVault_{int(time.time() * 1000)}"
        proj = start_project_intake(p_name, "Document indexing and archiving tool")
        self.assertEqual(proj["status"], "prd_ready")
        p_id = proj["project_id"]

        # 2. Approve PRD
        appr = approve_project_prd(p_id)
        self.assertTrue(appr["success"])

        # 3. Advance to completion (runs Sprints 1 through 5)
        res = advance_project_to_completion(p_id)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "completed")

        # 4. Check summary
        summary = get_project_summary(p_id)
        self.assertEqual(summary["status"], "completed")
        self.assertEqual(len(summary["sprints"]), 5)

        # 5. Check morning standup report text
        standup_text = get_morning_standup_report()
        self.assertIsNotNone(standup_text)
        self.assertIn("engineering front", standup_text.lower())

    def test_web_application_full_lifecycle(self):
        p_name = f"WebStudio_{int(time.time() * 1000)}"
        custom_answers = {
            "platform": "Responsive Web Application",
            "core_features": "Interactive portfolio, gallery, and contact form"
        }
        proj = start_project_intake(p_name, "Build an interactive agency website", custom_answers)
        self.assertEqual(proj["status"], "prd_ready")
        p_id = proj["project_id"]

        # Approve and advance to completion
        approve_project_prd(p_id)
        res = advance_project_to_completion(p_id)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "completed")

        # Verify artifacts exist on disk
        root = proj["root_dir"]
        self.assertTrue(os.path.exists(os.path.join(root, "templates", "index.html")))
        self.assertTrue(os.path.exists(os.path.join(root, "templates", "admin.html")))
        self.assertTrue(os.path.exists(os.path.join(root, "static", "css", "style.css")))
        self.assertTrue(os.path.exists(os.path.join(root, "static", "js", "main.js")))
        self.assertTrue(os.path.exists(os.path.join(root, "app.py")))
        self.assertTrue(os.path.exists(os.path.join(root, "run.bat")))
        self.assertTrue(os.path.exists(os.path.join(root, "tests", "test_web.py")))
        self.assertTrue(os.path.exists(os.path.join(root, "README.md")))

        # Verify modern web baseline standards compliance
        with open(os.path.join(root, "templates", "index.html"), "r", encoding="utf-8") as f:
            html = f.read().lower()
        self.assertIn("<dialog", html)
        self.assertIn("inquirymodal", html)

        with open(os.path.join(root, "static", "css", "style.css"), "r", encoding="utf-8") as f:
            css = f.read()
        self.assertIn(":has(", css)
        self.assertIn("::backdrop", css)

    def test_change_request_workflow(self):
        p_name = f"WebCR_{int(time.time() * 1000)}"
        custom_answers = {
            "platform": "Responsive Web Application",
            "core_features": "Agency portfolio with dark mode and contact form"
        }
        proj = start_project_intake(p_name, "Build full responsive studio website", custom_answers)
        p_id = proj["project_id"]
        approve_project_prd(p_id)
        advance_project_to_completion(p_id)

        # 1. Testimonials Change Request
        cr1 = apply_change_request(p_id, "add testimonials section to the website")
        self.assertTrue(cr1["success"])
        self.assertTrue(cr1["qa_passed"])
        html_file = os.path.join(proj["root_dir"], "templates", "index.html")
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("testimonials", html.lower())

        # 2. Pricing Plans Change Request
        cr2 = apply_change_request(p_id, "add pricing plans")
        self.assertTrue(cr2["success"])
        self.assertTrue(cr2["qa_passed"])
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("pricing", html.lower())

        # 3. Theme Change Request
        cr3 = apply_change_request(p_id, "change theme to neon purple")
        self.assertTrue(cr3["success"])
        self.assertTrue(cr3["qa_passed"])
        css_file = os.path.join(proj["root_dir"], "static", "css", "style.css")
        with open(css_file, "r", encoding="utf-8") as f:
            css = f.read()
        self.assertIn("#a855f7", css)

        # 4. FAQ Section Change Request
        cr4 = apply_change_request(p_id, "add FAQ accordion to the website")
        self.assertTrue(cr4["success"])
        self.assertTrue(cr4["qa_passed"])
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("faq", html.lower())

        # 5. Universal Dynamic Section Synthesis (e.g. Roadmap)
        cr5 = apply_change_request(p_id, "add roadmap section to the website")
        self.assertTrue(cr5["success"])
        self.assertTrue(cr5["qa_passed"])
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("roadmap", html.lower())


class TestAgencySkillRouting(unittest.TestCase):
    """Test skill keywords and intent detection."""

    def test_can_handle_directives(self):
        self.assertTrue(agency_skill.can_handle("assemble team to build inventory tool"))
        self.assertTrue(agency_skill.can_handle("start project invoice generator"))
        self.assertTrue(agency_skill.can_handle("project standup"))
        self.assertTrue(agency_skill.can_handle("project status"))
        self.assertTrue(agency_skill.can_handle("approve PRD"))
        self.assertTrue(agency_skill.can_handle("list projects"))
        self.assertTrue(agency_skill.can_handle("launch website"))
        self.assertTrue(agency_skill.can_handle("preview project"))
        self.assertTrue(agency_skill.can_handle("stop website"))
        self.assertTrue(agency_skill.can_handle("stop server"))
        self.assertTrue(agency_skill.can_handle("add testimonials to website"))
        self.assertTrue(agency_skill.can_handle("add pricing table to the project"))
        self.assertTrue(agency_skill.can_handle("add FAQ section"))
        self.assertTrue(agency_skill.can_handle("add team section"))
        self.assertTrue(agency_skill.can_handle("change website theme"))

    def test_session_hijacking_guard(self):
        # When an interview session is active
        agency_skill.ACTIVE_INTAKE_SESSION = {
            "project_name": "TestSite",
            "stage": "discovery_interview",
            "timestamp": time.time()
        }
        try:
            # Common global commands must NOT be hijacked
            self.assertFalse(agency_skill.can_handle("what is the weather today"))
            self.assertFalse(agency_skill.can_handle("what time is it"))
            self.assertFalse(agency_skill.can_handle("play music"))
            self.assertFalse(agency_skill.can_handle("volume up"))

            # Requirements input MUST be handled
            self.assertTrue(agency_skill.can_handle("I want a dark modern photography portfolio"))
        finally:
            agency_skill.ACTIVE_INTAKE_SESSION = None

    def test_standup_execution(self):
        reply = agency_skill.execute("project standup")
        self.assertTrue(len(reply) > 10)

    def test_interactive_discovery_interview_flow(self):
        # 1. User says "assemble team to build a website"
        agency_skill.ACTIVE_INTAKE_SESSION = None
        reply = agency_skill.execute("assemble team to build a website")
        self.assertIn("initiated discovery", reply)
        self.assertIn("what pages, design style, or features do you want", reply)
        self.assertIsNotNone(agency_skill.ACTIVE_INTAKE_SESSION)
        self.assertEqual(agency_skill.ACTIVE_INTAKE_SESSION["stage"], "discovery_interview")

        # 2. User explains their ideas!
        reply2 = agency_skill.execute("I need a dark cyan portfolio with photography gallery and booking form")
        self.assertIn("Client requirements captured", reply2)
        self.assertIn("photography gallery and booking form", reply2)
        self.assertEqual(agency_skill.ACTIVE_INTAKE_SESSION["stage"], "awaiting_approval")

        # 3. User says "approve PRD"
        reply3 = agency_skill.execute("approve PRD")
        self.assertIn("approved", reply3.lower())

        # Reset session
        agency_skill.ACTIVE_INTAKE_SESSION = None


if __name__ == "__main__":
    unittest.main()
