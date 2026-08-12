
import time
import psutil
from voice_engine.voice import speak

def battery_monitor():

    while True:

        battery = psutil.sensors_battery()

        if battery:
            if battery.percent < 20:
                speak("Warning sir. Battery is below 20 percent.")

        time.sleep(300)