"""
JARVIS Desktop Auto-Pilot & Computer Use Controller
Combines Screen OCR Vision, Mouse Automation, and Keyboard Dictation
to allow autonomous interaction with Windows desktop applications.
"""

import time
import os
import mss
import pyautogui
import pyperclip
import pytesseract
from PIL import Image
from typing import Optional, Tuple
from system_layer.app_controller import open_app

# Set Tesseract path if available
TESSERACT_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_EXE):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def find_text_coordinates(target_text: str) -> Optional[Tuple[int, int]]:
    """
    Capture the active screen, run OCR, and locate the pixel coordinates
    of the target text or UI button label.
    """
    clean_target = target_text.lower().strip()
    if not clean_target:
        return None

    try:
        with mss.mss() as sct:
            # Primary monitor
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        n_boxes = len(data["text"])

        # 1. Single word exact or substring match
        target_words = clean_target.split()

        for i in range(n_boxes):
            word = data["text"][i].strip().lower()
            if not word:
                continue

            # Exact match or strong substring
            if word == clean_target or (len(clean_target) > 3 and clean_target in word):
                x = data["left"][i] + (data["width"][i] // 2)
                y = data["top"][i] + (data["height"][i] // 2)
                return (x, y)

        # 2. Multi-word phrase search across consecutive boxes
        if len(target_words) > 1:
            for i in range(n_boxes - len(target_words) + 1):
                phrase_matches = True
                for j in range(len(target_words)):
                    box_word = data["text"][i + j].strip().lower()
                    if target_words[j] not in box_word and box_word not in target_words[j]:
                        phrase_matches = False
                        break
                if phrase_matches:
                    x = data["left"][i] + (data["width"][i] // 2)
                    y = data["top"][i] + (data["height"][i] // 2)
                    return (x, y)

    except Exception as e:
        print(f"[AUTOPILOT OCR ERROR]: {e}")

    return None


def click_text_on_screen(target_text: str, click_type: str = "single") -> str:
    """
    Locate text or button on display using OCR and click it autonomously.
    """
    clean = target_text.strip()
    coords = find_text_coordinates(clean)

    if not coords:
        return f"I could not locate '{clean}' on the display, Sir."

    x, y = coords
    try:
        pyautogui.moveTo(x, y, duration=0.25)
        if click_type == "double":
            pyautogui.doubleClick()
            return f"Double-clicked {clean}, Sir."
        elif click_type == "right":
            pyautogui.rightClick()
            return f"Right-clicked {clean}, Sir."
        else:
            pyautogui.click()
            return f"Clicked {clean}, Sir."
    except Exception as e:
        return f"Error clicking {clean}: {e}"


def type_text(text: str, press_enter: bool = False) -> str:
    """
    Type text or dictate a paragraph into the currently focused window.
    Uses clipboard pasting for speed, unicode fidelity, and reliability.
    """
    clean = text.strip()
    if not clean:
        return "No text specified to type, Sir."

    try:
        old_clipboard = ""
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            pass

        pyperclip.copy(clean)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.05)

        if press_enter:
            pyautogui.press("enter")

        return f"Typed: {clean}"

    except Exception as e:
        print(f"[AUTOPILOT TYPE ERROR]: {e}")
        try:
            pyautogui.write(clean, interval=0.01)
            if press_enter:
                pyautogui.press("enter")
            return f"Typed: {clean}"
        except Exception as write_err:
            return f"Failed to type text: {write_err}"


def snap_window(direction: str) -> str:
    """Snap the active window left, right, or toggle state."""
    d = direction.lower().strip()
    try:
        if "left" in d:
            pyautogui.hotkey("win", "left")
            return "Window snapped left, Sir."
        elif "right" in d:
            pyautogui.hotkey("win", "right")
            return "Window snapped right, Sir."
        elif "max" in d or "up" in d:
            pyautogui.hotkey("win", "up")
            return "Window maximized, Sir."
        elif "min" in d or "down" in d:
            pyautogui.hotkey("win", "down")
            return "Window minimized, Sir."
        elif "restore" in d:
            pyautogui.hotkey("win", "down")
            return "Window restored, Sir."
    except Exception as e:
        return f"Could not snap window: {e}"
    return "Unknown window snap direction, Sir."


def show_desktop() -> str:
    """Minimize all windows and show desktop."""
    try:
        pyautogui.hotkey("win", "d")
        return "Displaying desktop, Sir."
    except Exception as e:
        return f"Could not show desktop: {e}"


def switch_window() -> str:
    """Switch to the next active application window."""
    try:
        pyautogui.hotkey("alt", "tab")
        return "Switched window, Sir."
    except Exception as e:
        return f"Could not switch window: {e}"


def open_and_type(app_name: str, text: str) -> str:
    """
    Autonomous multi-step task: Open application, wait for window focus,
    and type the requested text.
    """
    clean_app = app_name.strip()
    clean_text = text.strip()

    res = open_app(clean_app)
    time.sleep(0.8)  # Allow application window to load and focus
    type_res = type_text(clean_text)

    return f"Opened {clean_app} and typed content, Sir."
