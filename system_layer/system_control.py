import os
import webbrowser
import subprocess
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from memory_layer.memory import remember, recall
from program_finder import find_program
from system_layer.system_monitor import system_report

# ---- SMART APP DICTIONARY ----
APP_PATHS = {
    "calculator": "calc",
    "notepad": "notepad",
    "paint": "mspaint",
    "task manager": "taskmgr",
    "command prompt": "cmd",
    "chrome": "chrome",
    "edge": "msedge",
    "vscode": "code",
    "vs code": "code",
    "spotify": "spotify",
    "discord": "discord",
    "powerpoint": "powerpnt",
    "word": "winword",
    "excel": "excel"
}
WINDOWS_APPS = {
    "camera": "start microsoft.windows.camera:",
    "settings": "start ms-settings:",
    "whatsapp": "start whatsapp:",
}

def control_volume(action):

    speakers = AudioUtilities.GetSpeakers()
    interface = speakers.EndpointVolume
    volume = cast(interface, POINTER(IAudioEndpointVolume))

    current = volume.GetMasterVolumeLevelScalar()

    if action == "increase":
        volume.SetMasterVolumeLevelScalar(min(current + 0.1, 1.0), None)
        return "Increasing volume."

    elif action == "decrease":
        volume.SetMasterVolumeLevelScalar(max(current - 0.1, 0.0), None)
        return "Decreasing volume."

    elif action == "mute":
        volume.SetMute(1, None)
        return "Volume muted."
    
    elif action == "unmute":
        volume.SetMute(0, None)
        return "Volume unmuted."
    
    elif action == "max":
        volume.SetMasterVolumeLevelScalar(1.0, None)
        return "Volume set to maximum."

    return None


def open_application(app_name):
    try:
        subprocess.Popen(app_name)
        return f"Opening {app_name}."
    except:
        return None


def handle_system_commands(command):

    command = command.lower().strip()

    # ----- SYSTEM STATUS -----
    if "system status" in command or "system report" in command or "system performance" in command:
        return system_report()

    # ---- LOCK SYSTEM ----
    elif "lock screen" in command:
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Locking the system."

    # ---- VOLUME CONTROLS ----
    elif "increase" in command and "volume" in command:
        return control_volume("increase")

    elif "decrease" in command and "volume" in command:
        return control_volume("decrease")
    
    elif "unmute" in command and "volume" in command:
        return control_volume("unmute")

    elif "mute" in command and "volume" in command:
        return control_volume("mute")
    
    elif "max" in command and "volume" in command:
        return control_volume("max")

    # ---- FOLDER OPENING ----
    elif "open downloads" in command:
        os.startfile(os.path.join(os.path.expanduser("~"), "Downloads"))
        return "Opening Downloads folder."

    elif "open documents" in command:
        os.startfile(os.path.join(os.path.expanduser("~"), "Documents"))
        return "Opening Documents folder."

    elif "open desktop" in command:
        os.startfile(os.path.join(os.path.expanduser("~"), "Desktop"))
        return "Opening Desktop."

    # ---- MEMORY SYSTEM ----
    elif command.startswith("remember"):

        parts = command.replace("remember", "").strip()

        if " is " in parts:
            key, value = parts.split(" is ", 1)
            remember(key.strip(), value.strip())
            return f"I will remember that your {key.strip()} is {value.strip()}."

    elif command.startswith("what is my"):

        key = command.replace("what is my", "").strip()
        value = recall(key)

        if value:
            return f"Your {key} is {value}."
        return f"I do not remember your {key} yet."

    # ---- SMART APP / WEBSITE LAUNCHER ----
    elif command.startswith("open "):

        app_name = command.replace("open ", "").strip()

        # 1️⃣ Windows Store apps
        if app_name in WINDOWS_APPS:
            os.system(WINDOWS_APPS[app_name])
            return f"Opening {app_name}."

        # 2️⃣ Smart dictionary
        if app_name in APP_PATHS:
            try:
                subprocess.Popen(APP_PATHS[app_name])
                return f"Opening {app_name}."
            except:
                return f"I couldn't open {app_name}."

        # 3️⃣ Search installed programs
        program_path = find_program(app_name)

        if program_path:
            try:
                os.startfile(program_path)
                return f"Opening {app_name}."
            except:
                return f"I found {app_name} but couldn't open it."

        # 4️⃣ Otherwise treat as website
        site = app_name

        if "." not in site:
            site += ".com"

        url = "https://www." + site

        try:
            webbrowser.open(url)
            return f"Opening {site}."
        except:
            return "I could not open that website."

    return None