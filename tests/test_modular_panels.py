"""
Unit tests for J.A.R.V.I.S. Sci-Fi HUD Modular Panels Architecture.
"""

import unittest
import gui.panels as panels


class TestModularPanels(unittest.TestCase):
    def test_panels_exported(self):
        """Ensure all 6 modular HUD panels are exported from gui.panels."""
        expected_panels = [
            "TelemetryPanel",
            "ReactorPanel",
            "MediaPanel",
            "TodoPanel",
            "EnvironmentPanel",
            "ControlsPanel",
        ]
        for p in expected_panels:
            self.assertTrue(hasattr(panels, p), f"gui.panels missing {p}")

    def test_panel_class_callables(self):
        """Ensure each panel component is a valid callable class."""
        self.assertTrue(callable(panels.TelemetryPanel))
        self.assertTrue(callable(panels.ReactorPanel))
        self.assertTrue(callable(panels.MediaPanel))
        self.assertTrue(callable(panels.TodoPanel))
        self.assertTrue(callable(panels.EnvironmentPanel))
        self.assertTrue(callable(panels.ControlsPanel))


if __name__ == "__main__":
    unittest.main()
