import os

from system_layer.file_indexer import FILE_INDEX


def get_latest_file(extension=None):

    candidates = []

    for item in FILE_INDEX:

        path = item["path"]

        if extension:

            if not path.lower().endswith(extension):
                continue

        try:
            modified = os.path.getmtime(path)

            candidates.append(
                (modified, path)
            )

        except:
            pass

    if not candidates:
        return None

    candidates.sort(reverse=True)

    return candidates[0][1]


def open_latest_file(extension=None):

    latest = get_latest_file(extension)

    if not latest:
        return "No matching file found."

    os.startfile(latest)

    return f"Opening {os.path.basename(latest)}"