from ai_brain.ai_modes import activate_mode, MODES

skill = {
    "name": "Mode Skill",
    "description": "Activates AI personality modes",
    "priority": 30
}

def can_handle(command):
    cmd = command.lower().strip()
    if any(ex in cmd for ex in ["sentry", "stealth", "protocol", "night", "work", "voice", "piper"]):
        return False
    if "mode" in cmd or "mood" in cmd:
        return any(m in cmd for m in MODES.keys())
    return False


def execute(command):
    mode_name = command.replace("activate", "")
    mode_name = mode_name.replace("mode", "").replace("mood", "")
    mode_name = mode_name.strip()

    return activate_mode(mode_name)