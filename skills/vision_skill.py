from system_layer.vision_controller import (
    read_screen,
    take_screenshot,
    describe_screen,
    explain_error,
    explain_code,
    find_bugs,
    optimize_code,
    fix_code,
    add_comments,
    generate_documentation
)
skill = {
    "name": "Vision",
    "priority": 50
}

def can_handle(command):
    command = command.lower()

    keywords = [
        "read my screen",
        "read screen",
        "take screenshot",
        "screenshot",
        "capture screen",
        "describe my screen",
        "describe screen",
        "look at my screen",
        "look at the screen",
        "what's on my screen",
        "what is on my screen",
        "scan my screen",
        "scan screen",
        "see my screen",
        "analyze my screen",
        "analyze screen"
    ]

    if any(keyword in command for keyword in keywords):
        return True

    if "error" in command:
        return True

    if "explain" in command and "code" in command:
        return True

    if "bug" in command:
        return True

    if "optimize" in command or "optimise" in command:
        return True

    if "summarize" in command or "summarise" in command:
        return True

    if "fix this code" in command or "fix code" in command:
        return True

    if "comment" in command:
        return True

    if "documentation" in command or "document" in command:
        return True

    return False

def execute(command):
    command = command.lower()

    if "screenshot" in command or "capture screen" in command:
        return take_screenshot()

    if any(k in command for k in ["describe", "look at", "what is on", "what's on", "scan", "see", "analyze"]):
        return describe_screen()

    if "error" in command:
        return explain_error()

    if "explain" in command or "summarize" in command:
        return explain_code()

    if "bug" in command:
        return find_bugs()

    if "optimize" in command or "optimise" in command:
        return optimize_code()

    if "fix" in command:
        return fix_code()

    if "comment" in command:
        return add_comments()

    if "documentation" in command or "document" in command:
        return generate_documentation()

    return read_screen()