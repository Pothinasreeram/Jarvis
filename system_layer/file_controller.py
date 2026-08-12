import os
import subprocess

HOME = os.path.expanduser("~")

FOLDERS = {
    "desktop": os.path.join(HOME, "Desktop"),
    "downloads": os.path.join(HOME, "Downloads"),
    "documents": os.path.join(HOME, "Documents"),
    "pictures": os.path.join(HOME, "Pictures"),
    "videos": os.path.join(HOME, "Videos"),
    "music": os.path.join(HOME, "Music"),
    "onedrive": os.path.join(HOME, "OneDrive")
}


def open_folder(name):
    name = name.lower()

    if name not in FOLDERS:
        return None

    path = FOLDERS[name]

    if not os.path.exists(path):
        return f"{name.capitalize()} folder not found."

    subprocess.Popen(f'explorer "{path}"')

    return f"Opening {name}."