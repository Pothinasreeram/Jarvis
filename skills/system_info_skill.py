import platform
import psutil

# ============================================================
# JARVIS SYSTEM INFORMATION SKILL — V7.4.1
# ============================================================

skill = {
    "name": "System Information Skill",
    "priority": 25,
}


def can_handle(command):
    command = command.lower().strip()

    keywords = [
        "system status",
        "system information",
        "system info",
        "system health",
        "computer status",
        "computer information",
        "pc status",
        "pc information",
        "how is my system",
        "how is my computer",
        "cpu usage",
        "ram usage",
        "memory usage",
        "disk usage",
        "windows version",
    ]

    return any(keyword in command for keyword in keywords)


def execute(command):
    try:
        cpu = psutil.cpu_percent(interval=1)

        memory = psutil.virtual_memory()
        memory_percent = round(memory.percent)

        disk = psutil.disk_usage("/")
        disk_percent = round(disk.percent)

        system = platform.system()
        release = platform.release()

        battery = psutil.sensors_battery()

        if battery is not None:
            battery_percent = round(battery.percent)

            if battery.power_plugged:
                charging = "and the charger is connected"
            else:
                charging = "and the charger is disconnected"

            battery_info = (
                f"Battery is at {battery_percent} percent "
                f"{charging}."
            )
        else:
            battery_info = "Battery information is unavailable."

        return (
            f"System status: "
            f"CPU usage is {cpu} percent. "
            f"Memory usage is {memory_percent} percent. "
            f"Disk usage is {disk_percent} percent. "
            f"Operating system is {system} {release}. "
            f"{battery_info}"
        )

    except Exception as e:
        print("[SYSTEM INFO ERROR]", e)
        return "I couldn't retrieve the system information."