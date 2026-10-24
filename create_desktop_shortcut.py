import os
import win32com.client

project_dir = os.path.dirname(os.path.abspath(__file__))
pythonw_path = os.path.join(project_dir, '.venv', 'Scripts', 'pythonw.exe')
icon_path = os.path.join(project_dir, 'assets', 'icons', 'jarvis.ico')

desktop_candidates = [
    os.path.join(os.environ.get('USERPROFILE', ''), 'OneDrive', 'Desktop'),
    os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
]

shell = win32com.client.Dispatch('WScript.Shell')

for desktop in desktop_candidates:
    if os.path.exists(desktop):
        shortcut_path = os.path.join(desktop, 'J.A.R.V.I.S.lnk')
        shortcut = shell.CreateShortCut(shortcut_path)
        if os.path.exists(pythonw_path):
            shortcut.TargetPath = pythonw_path
            shortcut.Arguments = "main.py"
        else:
            shortcut.TargetPath = 'wscript.exe'
            shortcut.Arguments = f'"{os.path.join(project_dir, "Launch_JARVIS.vbs")}"'
        shortcut.WorkingDirectory = project_dir
        if os.path.exists(icon_path):
            shortcut.IconLocation = f'{icon_path},0'
        shortcut.Description = 'J.A.R.V.I.S. - Artificial Intelligence Desktop Assistant'
        shortcut.Save()
        print(f'Successfully updated desktop shortcut at: {shortcut_path}')
