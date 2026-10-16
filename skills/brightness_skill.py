import re
import screen_brightness_control as sbc


skill = {
    "name": "Screen Brightness Skill",
    "priority": 22,
}


def get_current_brightness():
    try:
        brightness = sbc.get_brightness()

        if isinstance(brightness, list):
            brightness = brightness[0]

        return int(brightness)

    except Exception as e:
        print("[BRIGHTNESS ERROR]", e)
        return None


def set_brightness(level):
    try:
        level = max(0, min(100, int(level)))
        sbc.set_brightness(level)
        return f"Screen brightness set to {level} percent."

    except Exception as e:
        print("[BRIGHTNESS ERROR]", e)
        return "I couldn't change the screen brightness."


def can_handle(command):
    command = command.lower().strip()

    keywords = [
        "brightness",
        "screen brightness",
        "display brightness",
        "make screen brighter",
        "make screen darker",
        "brighten screen",
        "dim screen",
    ]

    return any(keyword in command for keyword in keywords)


def execute(command):
    command = command.lower().strip()

    # ---------------- SET EXACT BRIGHTNESS ----------------

    match = re.search(r"(\d{1,3})\s*(?:percent|%)", command)

    if match and "brightness" in command:
        level = int(match.group(1))
        return set_brightness(level)


    # ---------------- MAXIMUM BRIGHTNESS ----------------

    if (
        "maximum brightness" in command
        or "max brightness" in command
        or "full brightness" in command
        or "brightest" in command
    ):
        return set_brightness(100)


    # ---------------- MINIMUM BRIGHTNESS ----------------

    if (
        "minimum brightness" in command
        or "min brightness" in command
        or "lowest brightness" in command
        or "darkest" in command
    ):
        return set_brightness(0)


    # ---------------- INCREASE BRIGHTNESS ----------------

    if (
        "increase brightness" in command
        or "increase the brightness" in command
        or "brightness up" in command
        or "brighter" in command
        or "brighten screen" in command
        or "make screen brighter" in command
    ):
        current = get_current_brightness()

        if current is None:
            return "I couldn't read the current screen brightness."

        return set_brightness(current + 10)


    # ---------------- DECREASE BRIGHTNESS ----------------

    if (
        "decrease brightness" in command
        or "decrease the brightness" in command
        or "brightness down" in command
        or "dimmer" in command
        or "dim screen" in command
        or "make screen darker" in command
    ):
        current = get_current_brightness()

        if current is None:
            return "I couldn't read the current screen brightness."

        return set_brightness(current - 10)


    # ---------------- CHECK BRIGHTNESS ----------------

    if (
        "current brightness" in command
        or "brightness level" in command
        or "what is my brightness" in command
        or "what's my brightness" in command
        or "check brightness" in command
    ):
        current = get_current_brightness()

        if current is None:
            return "I couldn't read the current screen brightness."

        return f"Screen brightness is currently {current} percent."


    return "I couldn't determine the requested brightness level."