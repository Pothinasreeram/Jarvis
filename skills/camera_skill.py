from system_layer.camera_controller import handle_camera_commands

skill = {
    "name": "Camera",
    "priority": 40
}


def can_handle(command):

    command = command.lower()

    keywords = [
        "camera",
        "open camera",
        "start camera",
        "webcam"
    ]

    return any(keyword in command for keyword in keywords)


def execute(command):
    return handle_camera_commands(command)