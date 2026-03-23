import os
import subprocess
import pyautogui
from vision import start_vision, stop_vision
from task_planner import execute_task_plan
from memory import remember, recall
import threading

def handle_automation(command):

    command = command.lower()
    plan = execute_task_plan(command)

    if plan:
       return plan
    
    if "activate vision" in command or "turn on camera" in command:
        threading.Thread(target=start_vision, daemon=True).start()
        return "Activating vision system."

    if "stop vision" in command or "turn off camera" in command:
        stop_vision()
        return "Vision system deactivated."
    # -------- MEMORY SYSTEM --------

    if "remember my project folder" in command:
        remember("project_folder", "C:\\Jarvis")
        return "I will remember your project folder."

    elif "open my project folder" in command:

        folder = recall("project_folder")

        if folder:
           os.startfile(folder)
           return "Opening your project folder."

        else:
           return "I don't know your project folder yet."
    # -------- OPEN FOLDERS --------

    if "open downloads" in command:
        os.startfile(os.path.expanduser("~/Downloads"))
        return "Opening downloads."

    elif "open documents" in command:
        os.startfile(os.path.expanduser("~/Documents"))
        return "Opening documents."

    elif "open desktop" in command:
        os.startfile(os.path.expanduser("~/Desktop"))
        return "Opening desktop."

    elif "open pictures" in command:
        os.startfile(os.path.expanduser("~/Pictures"))
        return "Opening pictures."

    # -------- OPEN APPLICATIONS --------

    elif "open vscode" in command or "open visual studio code" in command:
        subprocess.Popen("code")
        return "Opening Visual Studio Code."

    elif "open control panel" in command:
        os.system("control")
        return "Opening control panel."

    elif "open task manager" in command:
        os.system("taskmgr")
        return "Opening task manager."

    # -------- WINDOW CONTROL --------

    elif "minimize window" in command:
        pyautogui.hotkey("win", "down")
        return "Minimizing window."

    elif "maximize window" in command:
        pyautogui.hotkey("win", "up")
        return "Maximizing window."

    elif "show desktop" in command:
        pyautogui.hotkey("win", "d")
        return "Showing desktop."
    
    elif "optimize system" in command:
        os.system("cleanmgr")
        return "Opening system cleanup."

    return None