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
        "describe my screen",
        "describe screen"
    ]

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

    if "fix this code" in command:
        return True

    if "comment" in command:
        return True

    if "documentation" in command or "document" in command:
        return True

    return any(keyword in command for keyword in keywords)

def execute(command):
    command = command.lower()

    if "describe" in command:
        return describe_screen()

    if "screenshot" in command:
        return take_screenshot()

    if "error" in command:
        return explain_error()

    if "explain" in command :
        return explain_code()

    if "summarize" in command:
        return explain_code()

    if "bug" in command:
        return find_bugs()

    if "optimize" in command:
        return optimize_code()

    if "fix this code" in command :
        return fix_code()

    if "add comment" in command:
        return add_comments()

    if "generate documentation" in command:
        return generate_documentation()

    return read_screen()