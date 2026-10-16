"""
Voiceprint Biometric Skill for J.A.R.V.I.S.
Handles voice requests to enroll, verify, enable, and disable acoustic speaker identification.
"""

from system_layer.voiceprint_security import (
    enroll_user_voiceprint,
    verify_speaker,
    enable_voice_security,
    disable_voice_security,
    get_voiceprint_status
)

skill = {
    "name": "Voiceprint Skill",
    "priority": 16,
}

TRIGGER_KEYWORDS = [
    "enroll voiceprint",
    "enroll my voice",
    "calibrate voiceprint",
    "calibrate my voice",
    "record voiceprint",
    "verify voiceprint",
    "verify my voice",
    "voice biometric",
    "voiceprint security",
    "voice security status",
    "voiceprint status",
    "activate voice security",
    "enable voice security",
    "deactivate voice security",
    "disable voice security"
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if "voiceprint" in cmd:
        return True
    if "voice" in cmd and any(w in cmd for w in ["biometric", "enroll", "calibrate", "verify"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # 1. Enroll
    if any(w in cmd for w in ["enroll", "calibrate", "record", "learn"]):
        return enroll_user_voiceprint()

    # 2. Verify
    if "verify" in cmd or "check" in cmd and "status" not in cmd:
        matched, score, message = verify_speaker()
        return message

    # 3. Enable
    if any(w in cmd for w in ["activate", "enable", "start", "turn on"]) and "security" in cmd:
        return enable_voice_security()

    # 4. Disable
    if any(w in cmd for w in ["deactivate", "disable", "stop", "turn off"]) and "security" in cmd:
        return disable_voice_security()

    # 5. Status
    stat = get_voiceprint_status()
    enrolled_str = f"enrolled on {stat['enrolled_at']}" if stat['enrolled'] else "not yet enrolled"
    enabled_str = "armed" if stat['enabled'] else "disarmed"
    return f"Voiceprint Security Protocol is currently {enabled_str}. Authorized user template is {enrolled_str}, Sir."
