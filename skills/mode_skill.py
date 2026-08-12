from ai_brain.ai_modes import activate_mode

skill = {
    "name": "Mode Skill",
    "description": "Activates AI personality modes",
    "priority": 1
}

def can_handle(command):

    return "activate" in command and "mode" in command


def execute(command):

    mode_name = command.replace("activate", "")
    mode_name = mode_name.replace("mode", "")
    mode_name = mode_name.strip()

    return activate_mode(mode_name)