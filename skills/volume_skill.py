from system_layer.volume_controller import handle_volume_commands

skill = {
    "name": "Volume",
    "priority": 30
}


def can_handle(command):

    command = command.lower()

    keywords = [
        "volume",
        "mute",
        "unmute",
        "volume up",
        "volume down"
    ]

    return any(keyword in command for keyword in keywords)


def execute(command):
    return handle_volume_commands(command)