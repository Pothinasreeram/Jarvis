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


class TestAgencySkillRouting(unittest.TestCase):
    """Test skill keywords and intent detection."""

    def test_can_handle_directives(self):
        self.assertTrue(agency_skill.can_handle("assemble team to build inventory tool"))
        self.assertTrue(agency_skill.can_handle("start project invoice generator"))
        self.assertTrue(agency_skill.can_handle("project standup"))
        self.assertTrue(agency_skill.can_handle("project status"))
        self.assertTrue(agency_skill.can_handle("approve PRD"))
        self.assertTrue(agency_skill.can_handle("list projects"))

    def test_standup_execution(self):
        reply = agency_skill.execute("project standup")
        self.assertTrue(len(reply) > 10)


if __name__ == "__main__":
    unittest.main()
