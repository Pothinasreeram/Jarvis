import os

USER = os.path.expanduser("~")


def folder(name):
    onedrive = os.path.join(USER, "OneDrive", name)
    normal = os.path.join(USER, name)

    if os.path.exists(onedrive):
        return onedrive

    return normal


SEARCH_PATHS = [
    r"C:\Users\pothi\OneDrive\Documents",
    r"C:\Users\pothi\OneDrive\Desktop",
    r"C:\Users\pothi\OneDrive\Pictures",
    r"C:\Users\pothi\Downloads",
    r"C:\Users\pothi\OneDrive\Documents\Jarvis\screenshots"
]

FILE_INDEX = []


def build_index():
    global FILE_INDEX

    FILE_INDEX.clear()

    print("Building file index...")

    for folder in SEARCH_PATHS:
        
        if not os.path.exists(folder):
            continue

        print(f"Scanning: {folder}")

        for root, dirs, files in os.walk(folder):
            dirs[:] = [
                d for d in dirs
                if d not in {
                    "$RECYCLE.BIN",
                    "System Volume Information",
                    "__pycache__",
                    ".git",
                    "node_modules",
                    ".venv",
                    "venv",
                }
            ]

            for file in files:
                
                FILE_INDEX.append({
                    "name": file.lower(),
                    "path": os.path.join(root, file),
                })

    print(f"Indexed {len(FILE_INDEX)} files.")


def search_index(query):

    query = query.lower()

    matches = []

    for item in FILE_INDEX:

        if query in item["name"]:
            matches.append(item)

    return matches