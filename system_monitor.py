import psutil
import time
from voice import speak

last_warning_time = 0

def system_report():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()

    battery_text = f"{battery.percent}%" if battery else "N/A"

    return f"CPU usage is {cpu} percent, RAM usage is {ram} percent, battery is {battery_text}."


def system_watchdog():
    global last_warning_time

    while True:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        now = time.time()

        if (cpu > 90 or ram > 90) and (now - last_warning_time > 60):
            speak("Warning. System usage is critically high.")
            last_warning_time = now

        time.sleep(5)