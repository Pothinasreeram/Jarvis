"""
Voice Engine Switcher Skill for J.A.R.V.I.S.
Allows dynamic toggling between:
- 100% Offline Paul Bettany Neural Voice (Piper ONNX)
- Online British Neural Voice (Edge-TTS)
- Automatic Voice Routing
"""

import re
from voice_engine.voice import set_voice_mode, get_voice_mode
from voice_engine.piper_engine import is_piper_available

skill = {
    "name": "Voice Mode Skill",
    "priority": 24,
}

TRIGGER_KEYWORDS = [
    "switch to offline voice",
    "switch to online voice",
    "switch to auto voice",
    "enable offline voice",
    "enable online voice",
    "use offline voice",
    "use online voice",
    "paul bettany voice",
    "which voice are you using",
    "what voice are you using",
    "current voice mode",
    "toggle voice",
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    return any(kw in cmd for kw in TRIGGER_KEYWORDS) or (
        ("voice" in cmd or "speech" in cmd) and ("offline" in cmd or "online" in cmd or "bettany" in cmd)
    )


def execute(command: str) -> str:
    cmd = command.lower().strip()

    if "offline" in cmd or "bettany" in cmd or "local" in cmd:
        if not is_piper_available():
            return "Sir, the offline Piper neural engine is not ready on this system."
        msg = set_voice_mode("offline")
        return f"{msg} Running 100 percent locally on device."

    elif "online" in cmd or "cloud" in cmd or "edge" in cmd:
        msg = set_voice_mode("online")
        return f"{msg} Powered by British neural synthesis."

    elif "auto" in cmd or "automatic" in cmd:
        msg = set_voice_mode("auto")
        return f"{msg} I will use online neural speech when available, with instant local neural fallback."

    elif "which" in cmd or "what" in cmd or "current" in cmd:
        current = get_voice_mode()
        piper_ready = "available" if is_piper_available() else "not loaded"
        if current == "offline":
            return f"I am currently using the offline Paul Bettany neural voice. Local engine status: {piper_ready}."
        elif current == "online":
            return "I am currently using the online British neural voice."
        else:
            return f"Voice mode is set to automatic. Offline local engine is {piper_ready}."

    return "Voice engine status calibrated."
