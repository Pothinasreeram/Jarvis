import platform
import psutil
from system_layer.system_control import purge_system_ram

# ============================================================
# JARVIS SYSTEM INFORMATION SKILL — V7.4.2
# ============================================================

skill = {
    "name": "System Information Skill",
    "priority": 25,
}

PURGE_KEYWORDS = [
    "purge ram",
    "clean ram",
    "optimize memory",
    "free ram",
    "free up ram",
    "clear memory",
    "purge memory",
]

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
    ] + PURGE_KEYWORDS

    return any(keyword in command for keyword in keywords)


def execute(command):
    command_lower = command.lower().strip()

    if any(k in command_lower for k in PURGE_KEYWORDS):
        try:
            res = purge_system_ram()
            if res["freed_mb"] > 50:
                return (
                    f"Memory purge complete. Trimmed working sets across {res['processes_trimmed']} processes, "
                    f"freeing {res['freed_mb']} megabytes. Memory utilization is now {res['percent_after']} percent "
                    f"({res['used_gb']} of {res['total_gb']} gigabytes)."
                )
            else:
                return (
                    f"Memory optimization finished across {res['processes_trimmed']} processes. "
                    f"Active working sets trimmed. System memory load: {res['percent_after']} percent."
                )
        except Exception as e:
            print("[RAM PURGE ERROR]", e)
            return "Unable to complete memory purge."

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