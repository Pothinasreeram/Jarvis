"""
Unit tests for J.A.R.V.I.S. Lifecycle Coordinator and Structured Logger.
"""

import unittest
import os
import sys

# Ensure root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import core.logger as logger
from core.lifecycle import register_shutdown_hook, _shutdown_hooks


class TestLifecycleLogger(unittest.TestCase):
    def test_logger_methods(self):
        """Ensure all logger severity levels function without error."""
        logger.info("TEST", "Test info message")
        logger.warn("TEST", "Test warning message")
        logger.error("TEST", "Test error message")
        logger.success("TEST", "Test success message")
        logger.hud("HUD test message")

        # Verify log file was written
        self.assertTrue(os.path.exists(logger.LOG_FILE))
        with open(logger.LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Test info message", content)
            self.assertIn("Test warning message", content)

    def test_log_listener_callback(self):
        """Ensure subscribed listeners receive real-time log events."""
        received = []
        def listener(tag, level, msg):
            received.append((tag, level, msg))

        logger.add_log_listener(listener)
        logger.warn("SECURITY", "Unauthorized port access")
        logger.remove_log_listener(listener)

        self.assertTrue(any(tag == "SECURITY" and "Unauthorized" in msg for tag, lvl, msg in received))

    def test_shutdown_hook_registration(self):
        """Ensure shutdown hooks can be registered and stored cleanly."""
        hook_called = [False]
        def dummy_hook():
            hook_called[0] = True

        register_shutdown_hook(dummy_hook)
        self.assertIn(dummy_hook, _shutdown_hooks)


if __name__ == "__main__":
    unittest.main()
