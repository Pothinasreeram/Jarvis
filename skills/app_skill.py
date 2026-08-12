from system_layer.app_controller import open_app, close_app

skill = {
    "name": "Application Launcher",
    "priority": 35
}


def can_handle(command):
    command = command.lower()

    return (
        command.startswith("open ")
        or command.startswith("close ")
    )


def execute(command):
    command = command.lower()

    if command.startswith("open "):
        app = command.replace("open ", "").strip()
        return open_app(app)

    if command.startswith("close "):
        app = command.replace("close ", "").strip()
        return close_app(app)

    return None