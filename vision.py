"""
J.A.R.V.I.S. Real-Time Vision & Screen Intelligence Core
Powered by local Gemma3 Vision (Ollama) + Tesseract OCR + Fast Desktop Capture.
"""

import os
import io
import time
from datetime import datetime
from PIL import Image
import pytesseract
import pyautogui
import ollama

# Configure local Tesseract OCR
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

VISION_MODEL = "gemma3:4b"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def capture_screen(save_copy=False):
    """
    Capture the current desktop screen with multi-engine fail-safe.
    Returns a PIL Image object or None.
    """
    img = None

    # 1. Try PyAutoGUI / Pillow ImageGrab
    try:
        img = pyautogui.screenshot()
    except Exception as e:
        print("[VISION CAPTURE ERROR 1]:", e)

    # 2. Try MSS fallback
    if img is None:
        try:
            import mss
            with mss.mss() as sct:
                mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                sct_img = sct.grab(mon)
                img = Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')
        except Exception as e:
            print("[VISION CAPTURE ERROR 2]:", e)

    # 3. Fallback to latest saved screenshot if running headless/isolated
    if img is None:
        try:
            files = [os.path.join(SCREENSHOTS_DIR, f) for f in os.listdir(SCREENSHOTS_DIR) if f.endswith(".png")]
            if files:
                latest = max(files, key=os.path.getctime)
                img = Image.open(latest)
        except Exception:
            pass

    if img is None:
        print("[VISION ERROR]: Unable to capture active screen buffer.")
        return None

    if save_copy:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        img.save(filepath)
        print(f"[VISION] Screenshot saved to: {filepath}")

    return img


def save_screenshot():
    """Takes a screenshot and saves it to the screenshots directory."""
    img = capture_screen(save_copy=True)
    if img:
        return "Screenshot captured and saved to your screenshots archive, Sir."
    return "I was unable to capture a screenshot at this moment, Sir."


def read_screen_text():
    """Extract all visible text from the screen using Tesseract OCR."""
    img = capture_screen()
    if img is None:
        return "I cannot access the display buffer right now, Sir."

    try:
        text = pytesseract.image_to_string(img)
        cleaned = text.strip()
        if not cleaned:
            return "No readable text was detected on the active display."
        return f"Here is the text detected on your screen:\n\n{cleaned[:2000]}"
    except Exception as e:
        print("[OCR ERROR]:", e)
        return "An error occurred during OCR text extraction, Sir."


def analyze_screen(prompt="Describe what is visible on this screen in 2 to 3 concise sentences."):
    """
    Analyzes the current screen using the local multimodal vision model (Gemma3 4B).
    Provides visual reasoning, error diagnosis, and UI breakdown.
    """
    img = capture_screen()
    if img is None:
        return "I could not capture your screen buffer, Sir. Please ensure JARVIS has display access."

    try:
        # Resize image for fast inference (max 1024x1024, JPEG quality 85)
        img_copy = img.copy()
        img_copy.thumbnail((1024, 1024))
        buf = io.BytesIO()
        img_copy.save(buf, format="JPEG", quality=85)
        img_bytes = buf.getvalue()

        # Call local Ollama multimodal vision
        response = ollama.chat(
            model=VISION_MODEL,
            messages=[{
                "role": "user",
                "content": f"""You are J.A.R.V.I.S., Tony Stark's AI assistant. 
Analyze the user's active screen based on this request:
{prompt}

Keep your answer natural, direct, concise, and suitable for text-to-speech. Do not include markdown tables or excessive bullet points.""",
                "images": [img_bytes]
            }],
            options={
                "temperature": 0.2,
                "num_predict": 180
            }
        )

        analysis = response.get("message", {}).get("content", "").strip()
        if not analysis:
            analysis = "I scanned the display, but could not discern meaningful content."
        return analysis

    except Exception as e:
        print("[VISION AI ERROR]:", e)
        # Fallback to OCR + LLM text analysis
        print("[VISION] Falling back to OCR text analysis...")
        ocr_text = read_screen_text()
        from ai_brain.ai_brain import ask_ai
        return ask_ai(f"User asked: {prompt}. Here is the visible text on the screen: {ocr_text}")