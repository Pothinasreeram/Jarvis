from system_layer.browser_controller import handle_browser_commands

skill = {
    "name": "Browser",
    "priority": 50
}


def can_handle(command):
    command = command.lower().strip()
    return (
        command.startswith("google ")
        or command.startswith("search google ")
        or "youtube" in command
        or (command.startswith("open ") and any(s in command for s in ["google", "youtube", "github", "reddit", "wikipedia", "amazon", "gmail", "chatgpt", "website"]))
    )


def execute(command):
    return handle_browser_commands(command)