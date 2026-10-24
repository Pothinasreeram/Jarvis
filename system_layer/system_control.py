import os
import webbrowser
import subprocess
import gc
import ctypes
from ctypes import cast, POINTER
import psutil
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from memory_layer.memory import remember, recall
from program_finder import find_program
from system_layer.system_monitor import system_report

def purge_system_ram():
    """
    Cleans up physical memory by invoking Python garbage collection
    and trimming the working set of user-accessible processes via Windows PSAPI.
    Returns dict with processes_trimmed, freed_mb, freed_gb, percent_after, used_gb, total_gb.
    """
    gc.collect()
    mem_before = psutil.virtual_memory().used
    count = 0

    try:
        cur_h = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.psapi.EmptyWorkingSet(cur_h)
        count += 1
    except Exception:
        pass

    for proc in psutil.process_iter(['pid']):
        try:
            pid = proc.info.get('pid')
            if not pid or pid <= 4:
                continue
            h = ctypes.windll.kernel32.OpenProcess(0x0100 | 0x0400, False, pid)
            if h:
                ctypes.windll.psapi.EmptyWorkingSet(h)
                ctypes.windll.kernel32.CloseHandle(h)
                count += 1
        except Exception:
            pass

    mem_info = psutil.virtual_memory()
    freed_bytes = max(0, mem_before - mem_info.used)
    freed_mb = freed_bytes / (1024 * 1024)

    return {
        "processes_trimmed": count,
        "freed_mb": round(freed_mb, 1),
        "freed_gb": round(freed_mb / 1024.0, 2),
        "percent_after": round(mem_info.percent),
        "used_gb": round(mem_info.used / (1024**3), 1),
        "total_gb": round(mem_info.total / (1024**3), 1),
    }

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

    # ----- SYSTEM STATUS & RAM PURGE -----
    if "system status" in command or "system report" in command or "system performance" in command:
        return system_report()

    elif any(k in command for k in ["purge ram", "clean ram", "optimize memory", "free ram", "clear memory", "free up ram"]):
        res = purge_system_ram()
        if res["freed_mb"] > 50:
            return f"RAM purge complete. Trimmed {res['processes_trimmed']} processes, freeing {res['freed_mb']} megabytes. Memory utilization lowered to {res['percent_after']} percent."
        else:
            return f"RAM optimization completed across {res['processes_trimmed']} processes. Working sets trimmed. Memory utilization is {res['percent_after']} percent."

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