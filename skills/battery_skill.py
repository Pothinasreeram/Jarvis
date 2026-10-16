import psutil


# ============================================================
# JARVIS BATTERY SKILL — V7.2.4
# ============================================================

skill = {
    "name": "Battery Skill",
    "priority": 20,
}


def can_handle(command):
    """
    Check whether this skill should handle the command.
    """

    command = command.lower().strip()

    battery_keywords = [
        "battery",
        "battery status",
        "battery percentage",
        "battery level",
        "how much battery",
        "how much charge",
        "charge level",
        "charging status",
    ]

    return any(
        keyword in command
        for keyword in battery_keywords
    )


def execute(command):
    """
    Return the REAL battery status from Windows.
    """

    battery = psutil.sensors_battery()

    if battery is None:
        return "I couldn't access the battery information."

    percent = round(battery.percent)

    if battery.power_plugged:
        charging_status = "and the charger is connected."
    else:
        charging_status = "and the charger is disconnected."

    return (
        f"Your battery is at {percent} percent "
        f"{charging_status}"
    )