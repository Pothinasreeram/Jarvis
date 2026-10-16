"""
Desk Ergonomics & Health Coach Voice Skill for J.A.R.V.I.S.
Handles voice requests for screen-time tracking, posture checks,
and daily hydration logging.
"""

import re
from background_tasks.wellness_monitor import (
    start_wellness_monitor,
    stop_wellness_monitor,
    is_wellness_active,
    log_water_intake,
    get_hydration_count,
    reset_hydration,
    get_wellness_summary,
    get_ergonomic_advice,
    DAILY_WATER_TARGET
)

skill = {
    "name": "Wellness Skill",
    "priority": 25,
}

TRIGGER_KEYWORDS = [
    "wellness protocol",
    "wellness status",
    "wellness report",
    "posture check",
    "posture tip",
    "ergonomic",
    "ergonomics",
    "glass of water",
    "drank water",
    "log water",
    "hydration",
    "water intake",
    "how long have i been working",
    "screen time",
    "health check",
    "health status"
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if "water" in cmd and any(a in cmd for a in ["log", "drank", "drink", "status", "count", "glass"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # 1. Activation / Deactivation
    if any(w in cmd for w in ["activate", "start", "enable", "turn on"]) and any(w in cmd for w in ["wellness", "health", "ergonomic"]):
        return start_wellness_monitor()

    if any(w in cmd for w in ["deactivate", "stop", "disable", "turn off"]) and any(w in cmd for w in ["wellness", "health", "ergonomic"]):
        return stop_wellness_monitor()

    # 2. Log Water Intake
    if ("log" in cmd or "drank" in cmd or "had" in cmd or "add" in cmd) and "water" in cmd:
        # Check if quantity specified (e.g. "log 2 glasses of water")
        match = re.search(r'(\d+)\s+(?:glasses?|cups?)\s+of\s+water', cmd)
        glasses = 1
        if match:
            try:
                glasses = int(match.group(1))
            except Exception:
                glasses = 1
        return log_water_intake(glasses)

    # 3. Reset Hydration
    if "reset" in cmd and ("water" in cmd or "hydration" in cmd):
        return reset_hydration()

    # 4. Hydration Status
    if any(w in cmd for w in ["hydration", "water"]) and any(w in cmd for w in ["status", "how much", "count", "intake", "level"]):
        count = get_hydration_count()
        remaining = max(0, DAILY_WATER_TARGET - count)
        if count >= DAILY_WATER_TARGET:
            return f"You have logged {count} glasses of water today, Sir. Target achieved. Your hydration is optimal."
        else:
            return f"You have logged {count} of {DAILY_WATER_TARGET} glasses of water today, Sir. {remaining} more glasses recommended before end of day."

    # 5. Posture Check & Ergonomic Advice
    if any(w in cmd for w in ["posture", "ergonomic", "stretch"]):
        advice = get_ergonomic_advice()
        return f"Ergonomic Protocol Check: {advice}"

    # 6. Overall Wellness Report / Continuous Screen Time
    if any(w in cmd for w in ["wellness", "health", "screen time", "how long have i been working"]):
        summary = get_wellness_summary()
        status_word = "active" if summary["active"] else "inactive"
        return (
            f"Wellness Protocol is currently {status_word}, Sir. "
            f"You have been at the desk for {summary['continuous_work_str']} of continuous active time. "
            f"You have taken {summary['breaks_today']} breaks and logged {summary['glasses_today']} of {summary['daily_target']} glasses of water today."
        )

    # Fallback to advice
    return get_ergonomic_advice()
