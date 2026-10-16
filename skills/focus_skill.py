"""
Focus & Deep Work Enforcer Skill for J.A.R.V.I.S.
Handles voice commands to start/stop timed focus sessions, check remaining time,
and command Jarvis to close detected distraction windows.
"""

import re
from background_tasks.focus_guard import (
    start_focus_session,
    stop_focus_session,
    get_focus_status,
    close_pending_distraction,
)

skill = {
    "name": "Focus Guard Skill",
    "priority": 25,
}

TRIGGER_KEYWORDS = [
    "focus session",
    "focus mode",
    "deep work",
    "pomodoro",
    "start focus",
    "stop focus",
    "end focus",
    "focus status",
    "how much time left in focus",
    "close it",
    "yes close it",
    "close that window",
    "close the app",
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if ("focus" in cmd or "deep work" in cmd) and any(w in cmd for w in ["start", "begin", "activate", "stop", "end", "status", "time"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # 1. User says "yes close it" or "close it" in response to distraction prompt
    if any(kw in cmd for kw in ["close it", "yes close", "close that", "close the app", "close distracting"]):
        status = get_focus_status()
        if status.get("active"):
            success = close_pending_distraction()
            if success:
                return "Distracting window closed. Back to your focus, Sir."
            else:
                return "I couldn't locate that window, Sir, but stay focused."

    # 2. Stop / Cancel Focus
    if any(kw in cmd for kw in ["stop", "end", "cancel", "deactivate"]):
        return stop_focus_session()

    # 3. Check Focus Status / Remaining Time
    if any(kw in cmd for kw in ["status", "time left", "remaining", "how long"]):
        status = get_focus_status()
        if not status.get("active"):
            return "There is no focus session currently active, Sir."
        rem_str = status.get("remaining_str", "00:00")
        blocked = status.get("distractions_intercepted", 0)
        return f"Focus session is active with {rem_str} remaining. {blocked} distractions intercepted so far."

    # 4. Start Focus Session (extract minutes if specified)
    minutes = 25  # Standard Pomodoro default
    match = re.search(r'(\d+)\s*(?:minute|min|m\b)', cmd)
    if match:
        try:
            parsed = int(match.group(1))
            if 1 <= parsed <= 180:
                minutes = parsed
        except ValueError:
            pass

    return start_focus_session(minutes=minutes)
