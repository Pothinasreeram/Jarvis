"""
Sentry Mode & Desk Sentinel Skill for J.A.R.V.I.S.
Handles voice requests to engage/disengage desk presence monitoring and lock workstation.
"""

import re
import ctypes
from background_tasks.sentry_guard import (
    start_sentry_mode,
    stop_sentry_mode,
    get_sentry_status,
)
from voice_engine.sound_effects import play_fx

skill = {
    "name": "Sentry Skill",
    "priority": 15,
}

TRIGGER_KEYWORDS = [
    "sentry mode",
    "sentry mood",
    "activate sentry mode",
    "activate sentry mood",
    "start sentry mode",
    "start sentry mood",
    "enable sentry mode",
    "enable sentry mood",
    "deactivate sentry mode",
    "deactivate sentry mood",
    "stop sentry mode",
    "stop sentry mood",
    "disable sentry mode",
    "turn on sentry mode",
    "turn on sentry mood",
    "turn off sentry mode",
    "turn off sentry mood",
    "sentry status",
    "desk sentinel",
    "lock workstation",
    "lock computer",
    "lock my computer",
    "lock the pc",
    "lock pc",
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if "sentry" in cmd or "sentinel" in cmd:
        return True
    if "lock" in cmd and any(w in cmd for w in ["workstation", "computer", "pc", "screen"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # 1. Immediate Lock Workstation
    if "lock" in cmd and "sentry" not in cmd:
        play_fx("alert")
        try:
            ctypes.windll.user32.LockWorkStation()
            return "Workstation locked, Sir."
        except Exception as e:
            return f"Failed to lock workstation: {e}"

    # 2. Stop Sentry
    if any(w in cmd for w in ["stop", "deactivate", "disable", "off", "cancel"]):
        return stop_sentry_mode()

    # 3. Sentry Status
    if "status" in cmd or "which" in cmd:
        stat = get_sentry_status()
        if not stat.get("active"):
            return "Sentry Mode is currently in standby, Sir."
        state = stat.get("status", "PRESENT")
        secs = stat.get("seconds_since_seen", 0)
        return f"Sentry Mode is active. User presence is currently {state}. Last detected {secs} seconds ago."

    # 4. Start Sentry Mode (parse seconds if specified, default 90s)
    seconds = 90
    match = re.search(r'(\d+)\s*(?:second|sec|s\b)', cmd)
    if match:
        try:
            val = int(match.group(1))
            if 30 <= val <= 600:
                seconds = val
        except ValueError:
            pass

    return start_sentry_mode(auto_lock_seconds=seconds)
