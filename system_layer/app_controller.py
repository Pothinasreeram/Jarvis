import subprocess
import os

APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "paint": "mspaint",
    "cmd": "cmd",
    "powershell": "powershell",
    "explorer": "explorer",
    "settings": "start ms-settings:",
    "task manager": "taskmgr",
    "vscode": "code"
}


def open_app(name):
    name = name.lower()

    if name not in APPS:
        return "I don't know that application."

    try:
        app = APPS[name]

        if app.startswith("start "):
            os.system(app)
        else:
            subprocess.Popen(app)

        return f"Opening {name}."

    except Exception as e:
        return str(e)


def close_app(name):
    processes = {
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
        "notepad": "notepad.exe",
        "paint": "mspaint.exe",
        "calculator": "CalculatorApp.exe",
        "vscode": "Code.exe"
    }

    if name.lower() not in processes:
        return "I can't close that application."

    os.system(f'taskkill /F /IM "{processes[name.lower()]}"')

    return f"Closed {name}."