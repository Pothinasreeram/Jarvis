import os
import time
from datetime import datetime

import cv2
import numpy as np
import pyautogui
import pytesseract
import pyperclip
import pygetwindow as gw

from ai_brain.ai_brain import ask_ai

# -------------------------------------------------
# Tesseract
# -------------------------------------------------

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# -------------------------------------------------
# Capture VS Code Window
# -------------------------------------------------

def capture_code_window():

    try:
        windows = gw.getWindowsWithTitle("Visual Studio Code")

        if not windows:
            return pyautogui.screenshot()

        window = windows[0]

        if window.isMinimized:
            window.restore()

        window.activate()

        time.sleep(0.3)

        screenshot = pyautogui.screenshot(
            region=(
                window.left,
                window.top,
                window.width,
                window.height
            )
        )

        image = np.array(screenshot)

        height, width = image.shape[:2]

        # Remove Explorer (about 22% of width)
        crop = int(width * 0.22)

        image = image[:, crop:]

        return image

    except Exception as e:

        print("Window Capture Error:", e)

        return pyautogui.screenshot()


# -------------------------------------------------
# Copy Code Directly From VS Code
# -------------------------------------------------

def capture_code():

    try:

        windows = gw.getWindowsWithTitle("Visual Studio Code")

        if not windows:
            return None

        window = windows[0]

        if window.isMinimized:
            window.restore()

        window.activate()

        time.sleep(0.5)

        # Save clipboard
        old_clipboard = pyperclip.paste()

        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.2)

        pyautogui.hotkey("ctrl", "c")

        code = ""

        # Wait until clipboard changes
        for _ in range(10):

            time.sleep(0.1)

            code = pyperclip.paste()

            if code != old_clipboard:
                break

        # Restore clipboard
        pyperclip.copy(old_clipboard)

        if code and code.strip():

            return code

        return None

    except Exception as e:

        print("Clipboard Capture Error:", e)

        return None


# -------------------------------------------------
# OCR Fallback
# -------------------------------------------------

def read_screen():

    screenshot = capture_code_window()

    if isinstance(screenshot, np.ndarray):
        image = screenshot
    else:
        image = np.array(screenshot)

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    gray = cv2.medianBlur(
        gray,
        3
    )

    text = pytesseract.image_to_string(
        gray,
        config="--oem 3 --psm 6"
    )

    if not text.strip():

        return "No readable text found."

    return text[:5000]


# -------------------------------------------------
# Screenshot
# -------------------------------------------------

def take_screenshot():

    screenshot = pyautogui.screenshot()

    os.makedirs(
        "screenshots",
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y_%m_%d_%H_%M_%S"
    )

    filename = f"screenshot_{timestamp}.png"

    filepath = os.path.join(
        "screenshots",
        filename
    )

    screenshot.save(filepath)

    return f"Screenshot saved as {filename}"


# -------------------------------------------------
# Shared AI Helper
# -------------------------------------------------

def ask_about_screen(instruction):

    text = capture_code()

    if not text:

        text = read_screen()

    prompt = f"""
You are Jarvis.

The following content comes from Visual Studio Code.

If it is source code,
analyze it directly.

Ignore:

- Explorer
- Tabs
- Timeline
- Outline
- Folder names
- OCR mistakes
- Random symbols

Only focus on the source code.

{text}

{instruction}
"""

    return ask_ai(prompt, {})


# -------------------------------------------------
# Describe Screen
# -------------------------------------------------

def describe_screen():

    return ask_about_screen("""
Describe:

1. Which application is open.
2. What the user is doing.
3. Any visible errors.

Maximum 5 sentences.
""")


# -------------------------------------------------
# Explain Error
# -------------------------------------------------

def explain_error():

    return ask_about_screen("""
Find the programming error.

Return:

1. Error Type

2. Cause

3. Fix

4. Correct code example.
""")


# -------------------------------------------------
# Explain Code
# -------------------------------------------------

def explain_code():

    return ask_about_screen("""
Explain this code.

Include:

1. Purpose

2. Main functions

3. Workflow

4. Beginner-friendly explanation.
""")


# -------------------------------------------------
# Find Bugs
# -------------------------------------------------

def find_bugs():

    return ask_about_screen("""
Review this code.

Find:

- Syntax errors
- Logic errors
- Missing imports
- Bad practices
- Possible crashes

Explain each bug separately.
""")


# -------------------------------------------------
# Optimize Code
# -------------------------------------------------

def optimize_code():

    return ask_about_screen("""
Optimize this code.

Suggest:

- Better performance
- Better readability
- Better naming
- Better Python practices
- Better structure
""")


# -------------------------------------------------
# Fix Code
# -------------------------------------------------

def fix_code():

    return ask_about_screen("""
Fix every issue.

Return:

1. Problems found

2. Fully corrected code

3. Explanation of every fix.
""")


# -------------------------------------------------
# Add Comments
# -------------------------------------------------

def add_comments():

    return ask_about_screen("""
Rewrite the code with professional comments.

Explain every important section.

Return only the commented code.
""")


# -------------------------------------------------
# Documentation
# -------------------------------------------------

def generate_documentation():

    return ask_about_screen("""
Generate complete documentation.

Include:

- Purpose

- Functions

- Parameters

- Return values

- Workflow

- Example usage

Use Markdown.
""")