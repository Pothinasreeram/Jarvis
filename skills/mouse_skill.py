import pyautogui

skill = {
    "name": "Mouse Control Skill",
    "priority": 19,
}


def move_mouse(x=None, y=None, duration=0.2):
    try:
        current_x, current_y = pyautogui.position()

        if x is None:
            x = current_x

        if y is None:
            y = current_y

        pyautogui.moveTo(x, y, duration=duration)

        return f"Mouse moved to {x}, {y}."

    except Exception as e:
        print("[MOUSE ERROR]", e)
        return "I couldn't move the mouse."


def click_mouse(button="left"):
    try:
        pyautogui.click(button=button)
        return f"{button.capitalize()} click."

    except Exception as e:
        print("[MOUSE ERROR]", e)
        return f"I couldn't perform the {button} click."


def double_click():
    try:
        pyautogui.doubleClick()
        return "Double click."

    except Exception as e:
        print("[MOUSE ERROR]", e)
        return "I couldn't perform the double click."


def scroll_mouse(amount):
    try:
        pyautogui.scroll(amount)

        if amount > 0:
            return "Scrolled up."

        return "Scrolled down."

    except Exception as e:
        print("[MOUSE ERROR]", e)
        return "I couldn't scroll."


def move_relative(dx, dy):
    try:
        current_x, current_y = pyautogui.position()

        new_x = current_x + dx
        new_y = current_y + dy

        pyautogui.moveTo(new_x, new_y, duration=0.2)

        return f"Mouse moved to {new_x}, {new_y}."

    except Exception as e:
        print("[MOUSE ERROR]", e)
        return "I couldn't move the mouse."


def can_handle(command):
    command = command.lower().strip()

    keywords = [
        "move mouse",
        "move the mouse",
        "mouse left",
        "mouse right",
        "mouse up",
        "mouse down",
        "move cursor",
        "move the cursor",
        "click",
        "left click",
        "right click",
        "double click",
        "scroll up",
        "scroll down",
    ]

    return any(keyword in command for keyword in keywords)


def execute(command):
    command = command.lower().strip()

    # -----------------------------
    # -----------------------------
    # VISUAL OCR & MOUSE CLICKS
    # -----------------------------

    from system_layer.autopilot_controller import click_text_on_screen

    # Double click on text or current position
    if command.startswith("double click "):
        target = command.replace("double click ", "", 1).strip()
        if target:
            return click_text_on_screen(target, click_type="double")
        return double_click()

    if command == "double click":
        return double_click()

    # Right click on text or current position
    if command.startswith("right click "):
        target = command.replace("right click ", "", 1).strip()
        if target:
            return click_text_on_screen(target, click_type="right")
        return click_mouse("right")

    if command == "right click":
        return click_mouse("right")

    # Click on text/button or current position
    if command.startswith("click on ") or command.startswith("click "):
        target = command.replace("click on ", "", 1).replace("click ", "", 1).strip()
        if target and target not in ["here", "now", "mouse", "the mouse", "left"]:
            return click_text_on_screen(target, click_type="single")
        return click_mouse("left")

    if (
        command == "click"
        or "left click" in command
        or "click the mouse" in command
    ):
        return click_mouse("left")

    # -----------------------------
    # SCROLL
    # -----------------------------

    if "scroll up" in command:
        return scroll_mouse(5)

    if "scroll down" in command:
        return scroll_mouse(-5)

    # -----------------------------
    # RELATIVE MOVEMENT
    # -----------------------------

    movement_amount = 100

    if "mouse right" in command or "move mouse right" in command:
        return move_relative(movement_amount, 0)

    if "mouse left" in command or "move mouse left" in command:
        return move_relative(-movement_amount, 0)

    if "mouse up" in command or "move mouse up" in command:
        return move_relative(0, -movement_amount)

    if "mouse down" in command or "move mouse down" in command:
        return move_relative(0, movement_amount)

    # -----------------------------
    # SCREEN POSITIONS
    # -----------------------------

    screen_width, screen_height = pyautogui.size()

    if "center" in command:
        return move_mouse(
            screen_width // 2,
            screen_height // 2
        )

    if "top left" in command:
        return move_mouse(10, 10)

    if "top right" in command:
        return move_mouse(
            screen_width - 10,
            10
        )

    if "bottom left" in command:
        return move_mouse(
            10,
            screen_height - 10
        )

    if "bottom right" in command:
        return move_mouse(
            screen_width - 10,
            screen_height - 10
        )

    return "I couldn't determine the requested mouse action."