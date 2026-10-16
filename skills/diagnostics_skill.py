"""
Mark VII Diagnostics Voice Skill for J.A.R.V.I.S.
Handles voice requests for full system hardware telemetry, thermals, and core status.
"""

from system_layer.diagnostics_controller import format_spoken_diagnostics, get_hardware_telemetry

skill = {
    "name": "Diagnostics Skill",
    "priority": 24,
}

TRIGGER_KEYWORDS = [
    "diagnostics",
    "hardware diagnostics",
    "system diagnostics",
    "system health",
    "hardware status",
    "mark 7 diagnostics",
    "mark vii diagnostics",
    "thermal status",
    "cpu load",
    "gpu diagnostics",
    "performance diagnostics"
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if "diagnostic" in cmd:
        return True
    if any(w in cmd for w in ["system", "hardware"]) and any(w in cmd for w in ["health", "status", "profile", "report"]):
        return True
    return False


def execute(command: str) -> str:
    return format_spoken_diagnostics()
