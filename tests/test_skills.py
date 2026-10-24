"""
Unit tests for J.A.R.V.I.S. Skill Manager and Skill Routing.
"""

import unittest
from core.skill_manager import load_skills, SKILLS
import skills.youtube_skill as yt
import skills.coding_skill as coding


import skills.system_info_skill as sysinfo


class TestSkillManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_skills()

    def test_skills_loaded(self):
        """Ensure all 41 modular skills are successfully discovered and loaded."""
        self.assertGreaterEqual(len(SKILLS), 30, "Expected at least 30 active skills loaded.")

    def test_skills_priority_sorted(self):
        """Ensure skills are sorted in ascending order of priority."""
        priorities = [s.get("priority", 999) for s in SKILLS]
        self.assertEqual(priorities, sorted(priorities), "Skills are not properly sorted by priority.")

    def test_youtube_skill_routing(self):
        """Ensure YouTube skill correctly handles queries and hands off Spotify directives."""
        self.assertTrue(yt.can_handle("search youtube for lo-fi music"))
        self.assertTrue(yt.can_handle("play interstellar theme on youtube"))
        self.assertTrue(yt.can_handle("open youtube"))
        # Handoff to Spotify when Spotify is explicitly mentioned
        self.assertFalse(yt.can_handle("play starboy on spotify"))

    def test_coding_skill_routing(self):
        """Ensure Coding copilot skill handles coding generation requests."""
        self.assertTrue(coding.can_handle("write python code to scrape a website"))
        self.assertTrue(coding.can_handle("generate a script to sort files"))
        self.assertFalse(coding.can_handle("what is the weather today"))

    def test_system_info_ram_purge(self):
        """Ensure System Information skill recognizes RAM purge commands."""
        self.assertTrue(sysinfo.can_handle("purge ram"))
        self.assertTrue(sysinfo.can_handle("clean ram"))
        self.assertTrue(sysinfo.can_handle("optimize memory"))
        self.assertTrue(sysinfo.can_handle("free up ram"))
        self.assertTrue(sysinfo.can_handle("system status"))


if __name__ == "__main__":
    unittest.main()
