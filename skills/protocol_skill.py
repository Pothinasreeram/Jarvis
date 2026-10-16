"""
Custom Protocols Skill for J.A.R.V.I.S.
Handles voice commands to activate Work, Gaming, Night, and Stealth workflows.
"""

from system_layer.protocol_controller import (
    activate_work_protocol,
    activate_gaming_protocol,
    activate_night_protocol,
    activate_stealth_protocol,
    get_protocol_status,
)

skill = {
    "name": "Protocol Skill",
    "priority": 23,
}

TRIGGER_KEYWORDS = [
    "work protocol",
    "start work protocol",
    "activate work protocol",
    "work mode",
    "gaming protocol",
    "start gaming protocol",
    "activate gaming protocol",
    "gaming mode",
    "night protocol",
    "start night protocol",
    "activate night protocol",
    "night mode",
    "stealth protocol",
    "start stealth protocol",
    "activate stealth protocol",
    "stealth mode",
    "protocol status",
    "which protocol is active",
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if "protocol" in cmd and any(w in cmd for w in ["work", "game", "gaming", "night", "stealth", "status", "activate", "start"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    if "work" in cmd:
        return activate_work_protocol()
    elif "game" in cmd or "gaming" in cmd:
        return activate_gaming_protocol()
    elif "night" in cmd:
        return activate_night_protocol()
    elif "stealth" in cmd:
        return activate_stealth_protocol()
    elif "status" in cmd or "which" in cmd:
        return get_protocol_status()

    return "Protocol command received, Sir."
