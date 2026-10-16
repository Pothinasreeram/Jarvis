"""
JARVIS Window & Desktop Auto-Pilot Skill
Handles window snapping, switching, desktop toggling, and multi-step macros
like 'open notepad and type [text]'.
"""

import re
import pyautogui
from system_layer.autopilot_controller import snap_window, show_desktop, switch_window, open_and_type
from system_layer.app_controller import open_app

skill = {
    "name": "Application & Window Control Skill",
    "priority": 18,
}


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()

    # Multi-action macro
    if re.search(r"^open\s+([a-zA-Z0-9\s]+?)\s+and\s+(?:type|write)\s+(.+)", cmd):
        return True

    keywords = [
        "snap left",
        "snap right",
        "snap window left",
        "snap window right",
        "minimize window",
        "maximize window",
        "restore window",
        "close window",
        "switch window",
        "switch windows",
        "next window",
        "show desktop",
        "show the desktop",
    ]

    return any(k in cmd for k in keywords)


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # 1. Multi-step Macro: open [app] and type [text]
    macro_match = re.search(r"^open\s+([a-zA-Z0-9\s]+?)\s+and\s+(?:type|write)\s+(.+)", cmd)
    if macro_match:
        app_name = macro_match.group(1).strip()
        text_content = macro_match.group(2).strip()
        return open_and_type(app_name, text_content)

    # 2. Window Snapping
    if "snap left" in cmd or "snap window left" in cmd:
        return snap_window("left")

    if "snap right" in cmd or "snap window right" in cmd:
        return snap_window("right")

    if "maximize" in cmd:
        return snap_window("maximize")

    if "minimize" in cmd:
        return snap_window("minimize")

    if "restore" in cmd:
        return snap_window("restore")

    # 3. Window & Desktop Controls
    if "close window" in cmd:
        try:
            pyautogui.hotkey("alt", "f4")
            return "Closed window, Sir."
        except Exception as e:
            return f"Error closing window: {e}"

    if "switch window" in cmd or "switch windows" in cmd or "next window" in cmd:
        return switch_window()

    if "show desktop" in cmd or "show the desktop" in cmd:
        return show_desktop()

    return "I couldn't determine the requested window action, Sir."