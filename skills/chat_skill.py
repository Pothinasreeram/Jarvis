skill = {
    "name": "chat",
    "priority": 50
}

def can_handle(command):
    triggers = [
        "chat with me",
        "start chat"
    ]

    return any(trigger in command for trigger in triggers)

def execute(command):
    return "Chat mode activated"