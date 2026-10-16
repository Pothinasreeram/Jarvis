"""
JARVIS Game Launcher Skill
Handles commands like:
- "play game minecraft"
- "launch game cyberpunk"
"""

from system_layer.app_controller import open_app

skill = {
    "name": "Game",
    "priority": 36
}


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    return cmd.startswith("play game ") or cmd.startswith("launch game ")


def execute(command: str) -> str:
    cmd = command.lower().strip()
    if cmd.startswith("play game "):
        game = cmd.replace("play game ", "").strip()
    elif cmd.startswith("launch game "):
        game = cmd.replace("launch game ", "").strip()
    else:
        game = cmd

    return open_app(game)