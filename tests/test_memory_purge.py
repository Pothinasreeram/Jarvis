"""
Unit tests for J.A.R.V.I.S. Memory Purge and Windows PSAPI Working Set Optimizer.
"""

import unittest
from system_layer.system_control import purge_system_ram, handle_system_commands


class TestMemoryPurge(unittest.TestCase):
    def test_purge_system_ram_execution(self):
        """Ensure purge_system_ram executes cleanly and returns well-formed stats."""
        res = purge_system_ram()
        self.assertIsInstance(res, dict)
        self.assertIn("processes_trimmed", res)
        self.assertIn("freed_mb", res)
        self.assertIn("percent_after", res)
        self.assertIn("used_gb", res)
        self.assertIn("total_gb", res)
        self.assertGreaterEqual(res["processes_trimmed"], 1)
        self.assertGreater(res["total_gb"], 0)

    def test_handle_system_commands_purge(self):
        """Ensure system command router triggers RAM purge and returns informative text."""
        result = handle_system_commands("purge ram")
        self.assertIsNotNone(result)
        self.assertTrue("RAM" in result or "Memory" in result)
        self.assertTrue("percent" in result or "%" in result)


if __name__ == "__main__":
    unittest.main()
