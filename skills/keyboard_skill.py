import pyautogui


skill = {
    "name": "Keyboard & Input Control Skill",
    "priority": 20,
}


KEY_MAP = {
    "enter": "enter",
    "escape": "esc",
    "esc": "esc",
    "space": "space",
    "tab": "tab",
    "backspace": "backspace",
    "delete": "delete",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "home": "home",
    "end": "end",
    "page up": "pageup",
    "page down": "pagedown",
    "windows": "win",
    "windows key": "win",
    "win": "win",
}


def press_key(key):
    try:
        pyautogui.press(key)
        return f"Pressed {key}."
    except Exception as e:
        print("[KEYBOARD ERROR]", e)
        return f"I couldn't press {key}."


def hotkey_action(*keys):
    try:
        pyautogui.hotkey(*keys)
        return True
    except Exception as e:
        print("[KEYBOARD ERROR]", e)
        return False


def can_handle(command):
    command = command.lower().strip()

    # Dictation
    if command.startswith("type ") or command.startswith("write ") or command.startswith("dictate "):
        return True

    keywords = [
        "press enter",
        "press escape",
        "press esc",
        "press space",
        "press tab",
        "press backspace",
        "press delete",
        "press up",
        "press down",
        "press left",
        "press right",
        "press home",
        "press end",
        "press page up",
        "press page down",
        "press windows",
        "press windows key",
        "press win",
        "copy",
        "paste",
        "select all",
        "undo",
        "redo",
        "new tab",
        "close tab",
        "save file",
        "refresh",
        "reload",
        "close window",
        "zoom in",
        "zoom out",
    ]

    return any(keyword in command for keyword in keywords)


def execute(command):
    command = command.lower().strip()

    # -----------------------------
    # DICTATION / TYPING
    # -----------------------------
    from system_layer.autopilot_controller import type_text

    for prefix in ["type ", "write ", "dictate "]:
        if command.startswith(prefix):
            content = command[len(prefix):].strip()
            if content:
                res = type_text(content)
                return f"Typed content, Sir."
            return "Please tell me what you would like me to type, Sir."

    # -----------------------------
    # DESKTOP & BROWSER SHORTCUTS
    # -----------------------------
    if "new tab" in command:
        if hotkey_action("ctrl", "t"):
            return "Opened new tab, Sir."

    if "close tab" in command:
        if hotkey_action("ctrl", "w"):
            return "Closed tab, Sir."

    if command == "save" or "save file" in command:
        if hotkey_action("ctrl", "s"):
            return "Document saved, Sir."

    if "refresh" in command or "reload" in command:
        if hotkey_action("ctrl", "r"):
            return "Refreshed, Sir."

    if "close window" in command:
        if hotkey_action("alt", "f4"):
            return "Window closed, Sir."

    if "zoom in" in command:
        if hotkey_action("ctrl", "+") or hotkey_action("ctrl", "="):
            return "Zoomed in, Sir."

    if "zoom out" in command:
        if hotkey_action("ctrl", "-"):
            return "Zoomed out, Sir."

    # Clipboard shortcuts
    if command == "copy" or "copy that" in command:
        if hotkey_action("ctrl", "c"):
            return "Copied."
        return "I couldn't copy."

    if command == "paste" or "paste that" in command:
        if hotkey_action("ctrl", "v"):
            return "Pasted."
        return "I couldn't paste."

    # Selection
    if command == "select all" or "select everything" in command:
        if hotkey_action("ctrl", "a"):
            return "Selected all."
        return "I couldn't select everything."

    # Editing
    if command == "undo" or "undo that" in command:
        if hotkey_action("ctrl", "z"):
            return "Undone."
        return "I couldn't undo that."

    if command == "redo" or "redo that" in command:
        if hotkey_action("ctrl", "y"):
            return "Redone."
        return "I couldn't redo that."

    # Normal keys
    if command.startswith("press "):
        key_name = command.replace("press ", "", 1).strip()

        if key_name in KEY_MAP:
            return press_key(KEY_MAP[key_name])

    return "I couldn't determine the requested keyboard action."