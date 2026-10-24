"""
Autonomous Protocol Studio Skill for J.A.R.V.I.S.
Handles voice directives to trigger Work, Deep Focus, Night Coding, Meeting,
Clean Desk, and Stealth workstation workflows.
"""

from system_layer.protocol_controller import (
    execute_protocol,
    list_protocols,
    activate_work_protocol,
    activate_deep_focus_protocol,
    activate_night_protocol,
    activate_meeting_protocol,
    activate_clean_desk_protocol,
    activate_stealth_protocol,
    activate_gaming_protocol,
    get_protocol_status,
)

skill = {
    "name": "Protocol Skill",
    "priority": 23,
}

TRIGGER_KEYWORDS = [
    "work protocol",
    "activate work protocol",
    "work mode",
    "deep focus",
    "activate deep focus",
    "focus mode",
    "focus protocol",
    "night coding",
    "night protocol",
    "night mode",
    "meeting protocol",
    "meeting mode",
    "clean desk protocol",
    "clean desk mode",
    "stealth protocol",
    "stealth mode",
    "protocol status",
    "which protocol is active",
    "list protocols",
    "available protocols",
    "show protocols",
    "gaming protocol",
    "gaming mode",
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if "protocol" in cmd and any(w in cmd for w in ["work", "focus", "deep", "night", "meeting", "clean", "stealth", "game", "status", "list"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    if any(k in cmd for k in ["list", "available", "show protocols"]):
        return list_protocols()
    elif "status" in cmd or "which protocol" in cmd:
        return get_protocol_status()
    elif "deep focus" in cmd or "focus protocol" in cmd:
        return activate_deep_focus_protocol()
    elif "work" in cmd:
        return activate_work_protocol()
    elif "night" in cmd or "coding mode" in cmd:
        return activate_night_protocol()
    elif "meeting" in cmd:
        return activate_meeting_protocol()
    elif "clean" in cmd or "desk" in cmd:
        return activate_clean_desk_protocol()
    elif "stealth" in cmd or "privacy protocol" in cmd:
        return activate_stealth_protocol()
    elif "game" in cmd or "gaming" in cmd:
        return activate_gaming_protocol()
    elif "protocol" in cmd:
        words = cmd.split()
        for w in words:
            if w not in ["protocol", "activate", "start", "mode", "please", "jarvis"]:
                res = execute_protocol(w)
                if "not found" not in res:
                    return res
        return list_protocols()

    return "Protocol command received, Sir."
