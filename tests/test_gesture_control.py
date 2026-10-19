"""
Unit tests for J.A.R.V.I.S. Hand Gesture Control Subsystem.
"""

import unittest
from system_layer.gesture_controller import GestureController, gesture_controller
import skills.gesture_skill as gesture_skill


class MockLandmark:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class TestGestureControl(unittest.TestCase):
    def setUp(self):
        self.ctrl = GestureController()

    def test_initial_state(self):
        """Ensure controller initializes in idle inactive state."""
        self.assertFalse(self.ctrl.is_active())
        self.assertEqual(self.ctrl.get_last_gesture(), "NONE")

    def test_gesture_skill_can_handle(self):
        """Ensure voice directives for gestures are recognized by skill."""
        self.assertTrue(gesture_skill.can_handle("activate gesture control"))
        self.assertTrue(gesture_skill.can_handle("turn on hand gestures"))
        self.assertTrue(gesture_skill.can_handle("disable gesture mode"))
        self.assertTrue(gesture_skill.can_handle("gesture recognition status"))
        self.assertFalse(gesture_skill.can_handle("what is the weather"))

    def test_pinch_distance_logic(self):
        """Ensure pinch calculation identifies closed pinch vs open hand."""
        # 21 Mock landmarks
        landmarks_pinched = [MockLandmark(0.5, 0.5) for _ in range(21)]
        landmarks_pinched[4] = MockLandmark(0.50, 0.50) # Thumb
        landmarks_pinched[8] = MockLandmark(0.52, 0.51) # Index tip (dist ~0.022 < 0.055)

        self.ctrl._process_pinch(landmarks_pinched)
        self.assertTrue(self.ctrl._pinch_active)

        landmarks_open = [MockLandmark(0.5, 0.5) for _ in range(21)]
        landmarks_open[4] = MockLandmark(0.20, 0.20)
        landmarks_open[8] = MockLandmark(0.80, 0.80) # Far apart

        self.ctrl._process_pinch(landmarks_open)
        self.assertFalse(self.ctrl._pinch_active)


if __name__ == "__main__":
    unittest.main()
