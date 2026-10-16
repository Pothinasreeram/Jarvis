import os
import win32com.client

desktop_candidates = [
    os.path.join(os.environ.get('USERPROFILE', ''), 'OneDrive', 'Desktop'),
    os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
]
desktop = next((p for p in desktop_candidates if os.path.exists(p)), desktop_candidates[0])

project_dir = os.path.dirname(os.path.abspath(__file__))
target_vbs = os.path.join(project_dir, 'Launch_JARVIS.vbs')
icon_path = os.path.join(project_dir, 'assets', 'icons', 'jarvis.ico')
shortcut_path = os.path.join(desktop, 'J.A.R.V.I.S.lnk')

shell = win32com.client.Dispatch('WScript.Shell')
shortcut = shell.CreateShortCut(shortcut_path)
shortcut.TargetPath = 'wscript.exe'
shortcut.Arguments = f'"{target_vbs}"'
shortcut.WorkingDirectory = project_dir
shortcut.IconLocation = f'{icon_path},0'
shortcut.Description = 'J.A.R.V.I.S. - Artificial Intelligence Desktop Assistant'
shortcut.Save()

print(f'Successfully created desktop shortcut at: {shortcut_path}')
