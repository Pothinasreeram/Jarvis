from system_layer.browser_controller import handle_browser_commands

skill = {
    "name": "Browser",
    "priority": 50
}


def can_handle(command):

    command = command.lower()

    return (
        command.startswith("open ")
        or command.startswith("search ")
        or command.startswith("google ")
        or "youtube" in command
    )


def execute(command):
    return handle_browser_commands(command)