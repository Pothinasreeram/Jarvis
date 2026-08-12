from system_layer.file_controller import open_folder

from system_layer.file_search_controller import (
    find_file,
    open_match
)

from system_layer.latest_file_controller import (
    open_latest_file
)


# ============================================================
# FILE SKILL
# ============================================================

skill = {
    "name": "File Skill",
    "priority": 34
}


# ============================================================
# FOLDERS
# ============================================================

FOLDERS = [
    "downloads",
    "documents",
    "desktop",
    "pictures",
    "videos",
    "music",
    "onedrive"
]


# ============================================================
# FILE EXTENSIONS
# ============================================================

FILE_EXTENSIONS = [
    ".pdf",
    ".txt",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".zip",
    ".rar",
    ".csv",
    ".json"
]


# ============================================================
# FILE SEARCH INDICATORS
# ============================================================

FILE_WORDS = [
    "file",
    "files",
    "document",
    "documents",
    "pdf",
    "image",
    "images",
    "photo",
    "photos",
    "screenshot",
    "screenshots",
    "folder",
    "folders",
    "download",
    "downloads",
    "resume",
    "report"
]


# ============================================================
# CAN HANDLE
# ============================================================

def can_handle(command):

    command = command.lower().strip()

    # --------------------------------------------------------
    # Folder commands
    # --------------------------------------------------------

    if command.startswith("open "):

        if any(
            folder in command
            for folder in FOLDERS
        ):
            return True

        # Opening a known file type
        if any(
            extension in command
            for extension in FILE_EXTENSIONS
        ):
            return True

        # Explicit file wording
        if any(
            word in command
            for word in FILE_WORDS
        ):
            return True

    # --------------------------------------------------------
    # Find file commands
    # --------------------------------------------------------

    if command.startswith("find "):

        # Only handle it as a File Skill command
        # when the user is clearly talking about files.
        if any(
            word in command
            for word in FILE_WORDS
        ):
            return True

        if any(
            extension in command
            for extension in FILE_EXTENSIONS
        ):
            return True

        # Otherwise Project Search should handle it.
        return False

    # --------------------------------------------------------
    # Latest / newest file commands
    # --------------------------------------------------------

    if "latest pdf" in command:
        return True

    if "latest screenshot" in command:
        return True

    if "latest image" in command:
        return True

    if "newest download" in command:
        return True

    return False


# ============================================================
# EXECUTE
# ============================================================

def execute(command):

    command = command.lower().strip()

    # --------------------------------------------------------
    # LATEST FILES
    # --------------------------------------------------------

    if "latest pdf" in command:

        return open_latest_file(".pdf")


    if "latest screenshot" in command:

        return open_latest_file(".png")


    if "newest download" in command:

        return open_latest_file()


    if "latest image" in command:

        for ext in [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        ]:

            result = open_latest_file(ext)

            if "Opening" in result:
                return result

        return "No images found."


    # --------------------------------------------------------
    # OPEN FOLDER
    # --------------------------------------------------------

    if command.startswith("open "):

        for folder in FOLDERS:

            if folder in command:

                return open_folder(folder)


    # --------------------------------------------------------
    # FIND FILE
    # --------------------------------------------------------

    if command.startswith("find "):

        filename = command.replace(
            "find",
            "",
            1
        ).strip()

        matches = find_file(filename)

        if not matches:

            return f"I couldn't find {filename}."


        if len(matches) == 1:

            return open_match(
                matches[0]
            )


        message = (
            f"I found {len(matches)} "
            f"files.\n"
        )

        for i, match in enumerate(
            matches[:5],
            1
        ):

            message += (
                f"{i}. "
                f"{match['name']}\n"
            )

        message += (
            "Which one would you like "
            "to open?"
        )

        return {
            "type": "file_selection",
            "matches": matches[:5],
            "message": message
        }


    # --------------------------------------------------------
    # OPEN FILE
    # --------------------------------------------------------

    if command.startswith("open "):

        filename = command.replace(
            "open",
            "",
            1
        ).strip()

        if filename not in FOLDERS:

            matches = find_file(filename)

            if not matches:

                return (
                    f"I couldn't find "
                    f"{filename}."
                )


            if len(matches) == 1:

                return open_match(
                    matches[0]
                )


            message = (
                f"I found "
                f"{len(matches)} files.\n"
            )

            for i, match in enumerate(
                matches[:5],
                1
            ):

                message += (
                    f"{i}. "
                    f"{match['name']}\n"
                )

            message += (
                "Which one would you "
                "like to open?"
            )

            return {
                "type": "file_selection",
                "matches": matches[:5],
                "message": message
            }


    return None

