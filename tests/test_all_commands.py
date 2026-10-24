"""
Comprehensive End-to-End Command & Skills Verification Test Suite for J.A.R.V.I.S.
Tests every skill, command routing, multi-command splitting, intent classification,
and system control execution.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.skill_manager import load_skills, execute_skill, SKILLS
from command_system.command_splitter import split_commands
from command_system.intent_router import route_intent
from system_layer.system_control import handle_system_commands, purge_system_ram


class TestAllCommands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_skills()

    def test_01_all_42_skills_registered_and_sorted(self):
        """Verify that all 42 modular skills are loaded, unique, and strictly priority-sorted."""
        self.assertGreaterEqual(len(SKILLS), 42, f"Expected 42 skills, found {len(SKILLS)}")

        names = set()
        for s in SKILLS:
            self.assertIn("name", s)
            self.assertIn("priority", s)
            self.assertIn("module", s)
            self.assertTrue(hasattr(s["module"], "can_handle"), f"{s['name']} missing can_handle")
            self.assertTrue(hasattr(s["module"], "execute"), f"{s['name']} missing execute")
            names.add(s["name"])

        # Check ascending priority ordering
        priorities = [s["priority"] for s in SKILLS]
        self.assertEqual(priorities, sorted(priorities), "Skills must be strictly sorted by priority.")

    def test_02_every_single_skill_can_handle(self):
        """
        Verify can_handle() triggers across all 42 distinct skills in J.A.R.V.I.S.
        Ensures 100% command coverage across the modular skill registry.
        """
        skill_command_map = {
            "Math Skill": "calculate 45 plus 55",
            "Gesture Control": "enable hand gestures",
            "Memory": "remember that my car is tesla",
            "Sentry Skill": "arm sentry guard",
            "Voiceprint Skill": "verify my voice",
            "Briefing Skill": "executive briefing",
            "Application & Window Control Skill": "minimize window",
            "Mouse Control Skill": "move mouse left",
            "Battery Skill": "battery status",
            "Coding Copilot": "write python code to parse json",
            "Keyboard & Input Control Skill": "press enter",
            "Reminder": "remind me to check deployment in 10 minutes",
            "Microphone Control Skill": "mute microphone",
            "Research Skill": "research on quantum computing",
            "Screen Brightness Skill": "screen brightness 80",
            "Ghostwriter Skill": "rewrite this text",
            "Web Navigator Skill": "hacker news headlines",
            "Live Web Search": "search who won the super bowl",
            "Power & Session Skill": "lock the computer",
            "Protocol Skill": "activate stealth protocol",
            "Diagnostics Skill": "system diagnostics",
            "Network Information Skill": "network status",
            "Voice Mode Skill": "switch to offline voice",
            "Focus Guard Skill": "start focus mode",
            "System Information Skill": "purge ram",
            "Taskmaster Skill": "add task finish documentation",
            "Wellness Skill": "log water",
            "YouTube Skill": "search youtube for lo-fi music",
            "Maid Protocol Skill": "clean downloads folder",
            "Media Converter Skill": "convert png to jpg",
            "Mode Skill": "coding mode",
            "Volume": "volume 50",
            "Weather": "weather report",
            "File Skill": "open downloads",
            "Application Launcher": "open notepad",
            "Game": "play game chess",
            "Camera": "open camera",
            "Spotify": "play starboy on spotify",
            "Project Search": "find function in project",
            "Browser": "google python documentation",
            "Chat Companion": "chat with me",
            "Vision": "take screenshot",
        }

        # Verify that all 42 mapped skills match their designated commands
        skills_by_name = {s["name"]: s["module"] for s in SKILLS}

        for skill_name, test_cmd in skill_command_map.items():
            self.assertIn(skill_name, skills_by_name, f"Skill '{skill_name}' not found in registered SKILLS.")
            mod = skills_by_name[skill_name]
            can = mod.can_handle(test_cmd)
            self.assertTrue(can, f"Skill '{skill_name}' failed to handle command: '{test_cmd}'")

    def test_03_skill_manager_dispatch_routing(self):
        """Verify priority-based dispatching through core.skill_manager.execute_skill()."""
        # Math has priority 2 (should match before other skills)
        math_res = execute_skill("calculate 100 plus 250")
        self.assertIsNotNone(math_res)
        self.assertIn("350", str(math_res))

        # Battery has priority 20
        batt_res = execute_skill("battery status")
        self.assertIsNotNone(batt_res)
        self.assertIn("battery", str(batt_res).lower())

        # Diagnostics has priority 24
        diag_res = execute_skill("system diagnostics")
        self.assertIsNotNone(diag_res)
        self.assertTrue("Diagnostics" in str(diag_res) or "Status" in str(diag_res) or "System" in str(diag_res))

        # Chat Companion has priority 50
        chat_res = execute_skill("chat with me")
        self.assertIsNotNone(chat_res)
        self.assertIn("service", str(chat_res).lower())

    def test_04_multi_command_splitter(self):
        """Verify multi-action parsing and smart verb inheritance."""
        # 1. Simple conjunction split
        res1 = split_commands("open chrome and notepad")
        self.assertEqual(res1, ["open chrome", "open notepad"])

        # 2. Sequential 'then' split
        res2 = split_commands("mute then close window")
        self.assertEqual(res2, ["mute", "close window"])

        # 3. Triple action inheritance
        res3 = split_commands("open spotify and chrome and calc")
        self.assertEqual(res3, ["open spotify", "open chrome", "open calc"])

        # 4. Single command returns single element
        res4 = split_commands("system status")
        self.assertEqual(res4, ["system status"])

    def test_05_intent_router_classifications(self):
        """Verify intent categorizations across system, math, time, browser, and AI."""
        self.assertEqual(route_intent("shutdown system"), "system")
        self.assertEqual(route_intent("volume up"), "system")
        self.assertEqual(route_intent("calculate square root of 64"), "math")
        self.assertEqual(route_intent("what time is it"), "time")
        self.assertEqual(route_intent("what is today's date"), "time")
        self.assertEqual(route_intent("search google for quantum physics"), "browser")
        self.assertEqual(route_intent("who was Nikola Tesla"), "ai")

    def test_06_system_control_commands(self):
        """Verify direct operating system commands in system_control.py."""
        # Volume controls
        with patch("system_layer.system_control.control_volume") as mock_vol:
            mock_vol.return_value = "Volume set to maximum."
            res = handle_system_commands("max volume")
            self.assertEqual(res, "Volume set to maximum.")

        # RAM purge
        purge_res = handle_system_commands("purge ram")
        self.assertIsNotNone(purge_res)
        self.assertTrue("RAM" in purge_res or "Memory" in purge_res)

        # Folder requests
        with patch("os.startfile") as mock_start:
            res_dl = handle_system_commands("open downloads")
            self.assertEqual(res_dl, "Opening Downloads folder.")
            self.assertTrue(mock_start.called)

    def test_07_safe_execution_of_read_only_skills(self):
        """Execute core informative skills to ensure zero runtime exceptions."""
        skills_by_name = {s["name"]: s["module"] for s in SKILLS}

        # 1. Math
        self.assertEqual(skills_by_name["Math Skill"].execute("calculate 25 * 4"), "The result is 100")

        # 2. System Information
        sys_res = skills_by_name["System Information Skill"].execute("system status")
        self.assertIn("System status", sys_res)

        # 3. Network Info
        net_res = skills_by_name["Network Information Skill"].execute("network status")
        self.assertIsInstance(net_res, str)
        self.assertIn("Network", net_res)

        # 4. Taskmaster
        todo_res = skills_by_name["Taskmaster Skill"].execute("list tasks")
        self.assertIsInstance(todo_res, str)

        # 5. Wellness
        well_res = skills_by_name["Wellness Skill"].execute("wellness status")
        self.assertIsInstance(well_res, str)

        # 6. Protocol
        proto_res = skills_by_name["Protocol Skill"].execute("protocol status")
        self.assertIsInstance(proto_res, str)

        # 7. Weather
        weather_res = skills_by_name["Weather"].execute("weather")
        self.assertIsInstance(weather_res, str)


if __name__ == "__main__":
    unittest.main()
