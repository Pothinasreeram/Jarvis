"""
Executive Day Briefing Voice Skill for J.A.R.V.I.S.
Handles voice requests for "good morning", "morning briefing", "daily briefing", and day planning.
"""

from system_layer.briefing_controller import generate_executive_briefing

skill = {
    "name": "Briefing Skill",
    "priority": 18,
}

TRIGGER_KEYWORDS = [
    "good morning",
    "morning briefing",
    "daily briefing",
    "executive briefing",
    "day briefing",
    "start day briefing",
    "morning update",
    "daily update",
    "brief me",
    "morning report"
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if "briefing" in cmd:
        return True
    if "brief me" in cmd:
        return True
    return False


def execute(command: str) -> str:
    return generate_executive_briefing()
