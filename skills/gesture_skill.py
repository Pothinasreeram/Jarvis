"""
Hand Gesture Control Skill for J.A.R.V.I.S.
Enables or disables webcam neural gesture recognition (Open Palm, Victory, Thumbs Up/Down, Pinch).
"""

from system_layer.gesture_controller import gesture_controller
from voice_engine.voice import speak

skill = {
    "name": "Gesture Control",
    "priority": 15
}

TRIGGER_KEYWORDS = [
    "gesture control",
    "hand gesture",
    "hand gestures",
    "gesture mode",
    "gesture recognition"
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    return any(k in cmd for k in TRIGGER_KEYWORDS)


def execute(command: str) -> str:
    cmd = command.lower().strip()

    if any(w in cmd for w in ["activate", "enable", "start", "turn on"]):
        if gesture_controller.is_active():
            reply = "Hand gesture control is already active and monitoring camera input."
        else:
            msg = gesture_controller.start()
            reply = f"Hand gesture control engaged, Sir. {msg}"
        speak(reply)
        return reply

    elif any(w in cmd for w in ["deactivate", "disable", "stop", "turn off", "kill"]):
        if not gesture_controller.is_active():
            reply = "Hand gesture control is currently inactive."
        else:
            msg = gesture_controller.stop()
            reply = f"Hand gesture control disengaged. {msg}"
        speak(reply)
        return reply

    else:
        status = "Active and tracking" if gesture_controller.is_active() else "Offline"
        last = gesture_controller.get_last_gesture()
        reply = f"Gesture control is currently {status}. Last detected gesture was {last}."
        speak(reply)
        return reply
