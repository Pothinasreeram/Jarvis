"""
JARVIS Background Battery Monitor
Monitors system power status and provides proactive voice alerts:
- Warns once when battery drops below critical threshold (<= 18%) while unplugged.
- Confirms charging when plugged in after low battery.
- Resets warning state when battery recovers above 25%.
"""

import time
import threading
import psutil
from background_tasks.notification_manager import send_notification

BATTERY_CRITICAL_LEVEL = 18
BATTERY_RECOVERY_LEVEL = 25
CHECK_INTERVAL = 30  # check every 30s for prompt responsiveness

_battery_thread = None
_running = False


def battery_monitor(stop_event=None):
    """
    Continuous background loop for system battery health.
    """
    warning_sent = False
    was_low = False

    print("[BATTERY MONITOR] Proactive power intelligence online.")

    while True:
        if stop_event is not None and stop_event.is_set():
            print("[BATTERY MONITOR] Stop requested.")
            break

        try:
            battery = psutil.sensors_battery()
            if battery is not None:
                percent = round(battery.percent)
                plugged = bool(battery.power_plugged)

                # Low battery warning (only if unplugged)
                if percent <= BATTERY_CRITICAL_LEVEL and not plugged:
                    if not warning_sent:
                        send_notification(
                            f"Sir, battery level has dropped to {percent} percent. Please connect power."
                        )
                        warning_sent = True
                        was_low = True

                # Plugged in after warning
                elif plugged and was_low:
                    send_notification(
                        f"Power connected, Sir. Battery charging at {percent} percent."
                    )
                    was_low = False
                    warning_sent = False

                # Battery recovered above threshold
                elif percent >= BATTERY_RECOVERY_LEVEL:
                    warning_sent = False
                    was_low = False

        except Exception as e:
            print("[BATTERY MONITOR ERROR]:", e)

        # Interruptible sleep
        if stop_event is not None:
            if stop_event.wait(CHECK_INTERVAL):
                break
        else:
            time.sleep(CHECK_INTERVAL)

    print("[BATTERY MONITOR] Stopped.")


def start_battery_monitor(stop_event=None):
    """Start the battery monitor as a daemon thread."""
    global _battery_thread, _running
    if _battery_thread and _battery_thread.is_alive():
        return "Battery monitor already running."

    _running = True
    _battery_thread = threading.Thread(
        target=battery_monitor,
        args=(stop_event,),
        name="Jarvis-Battery-Monitor",
        daemon=True
    )
    _battery_thread.start()
    return "Battery monitor started."