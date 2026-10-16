"""
JARVIS Application & Game Launcher Skill
Handles voice commands:
- "open chrome"
- "launch vs code"
- "start calculator"
- "run task manager"
- "close discord"
"""

from system_layer.app_controller import open_app, close_app

skill = {
    "name": "Application Launcher",
    "priority": 35
}

PREFIXES_OPEN = ("open ", "launch ", "start ", "run ")
PREFIXES_CLOSE = ("close ", "kill ", "terminate ", "quit ", "exit ")


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    return any(cmd.startswith(p) for p in PREFIXES_OPEN + PREFIXES_CLOSE)


def execute(command: str) -> str:
    cmd = command.lower().strip()

    for p in PREFIXES_CLOSE:
        if cmd.startswith(p):
            target = cmd[len(p):].strip()
            return close_app(target)

    for p in PREFIXES_OPEN:
        if cmd.startswith(p):
            target = cmd[len(p):].strip()
            return open_app(target)

    return "Could not process application command, Sir."