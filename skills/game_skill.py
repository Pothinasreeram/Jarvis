skill = {
    "name": "Game",
    "priority": 50
}

def can_handle(command):
    command = command.lower()
    # Return True if this skill should handle the command
    return False

def execute(command):
    # Execute the command
    return "Done"