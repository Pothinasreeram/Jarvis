import os

# ============================================================
# JARVIS POWER & SESSION SKILL — V7.4.3
# ============================================================

skill = {
    "name": "Power & Session Skill",
    "priority": 23,
}


def can_handle(command):
    command = command.lower().strip()

    keywords = [
        "lock my computer",
        "lock the computer",
        "lock my pc",
        "lock the pc",
        "lock the system",
        "lock computer",
        "lock pc",
    ]

    return any(keyword in command for keyword in keywords)


def execute(command):
    command = command.lower().strip()

    if any(
        phrase in command
        for phrase in [
            "lock my computer",
            "lock the computer",
            "lock my pc",
            "lock the pc",
            "lock the system",
            "lock computer",
            "lock pc",
        ]
    ):
        try:
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return "Locking the computer."

        except Exception as e:
            print("[POWER SKILL ERROR]", e)
            return "I couldn't lock the computer."

    return "I couldn't determine the requested power operation."