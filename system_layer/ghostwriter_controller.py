"""
Voice Ghostwriter & Instant Clipboard AI Engine for J.A.R.V.I.S.
Captures highlighted on-screen text or clipboard content, refines it using local
LLaMA 3.1:8b (rewriting, grammar correction, translation, summarization),
and automatically pastes the polished text back into the active application.
"""

import time
import pyautogui
import pyperclip
import threading
from typing import Optional

from ai_brain.ai_brain import ask_ai
from voice_engine.sound_effects import play_fx

# Ensure pyautogui does not hang
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def _get_highlighted_or_clipboard_text() -> str:
    """
    Attempt to copy currently highlighted text via Ctrl+C.
    Falls back to existing clipboard content if nothing is selected.
    """
    backup_clip = ""
    try:
        backup_clip = pyperclip.paste()
    except Exception:
        pass

    # Clear clipboard to detect if Ctrl+C copied new text
    pyperclip.copy("")
    time.sleep(0.04)

    try:
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.08)
        selected_text = pyperclip.paste().strip()
        if selected_text:
            return selected_text
    except Exception as e:
        print(f"[GHOSTWRITER COPY ERROR]: {e}")

    # Fallback to previous clipboard text
    if backup_clip and backup_clip.strip():
        return backup_clip.strip()

    return ""


def process_ghostwriter_task(instruction_type: str, custom_instruction: str = "", auto_paste: bool = True) -> str:
    """
    Main Ghostwriter pipeline:
    1. Grabs text.
    2. Runs through LLaMA 3.1:8b with specialized direct-replacement prompt.
    3. Writes to clipboard and auto-pastes back via Ctrl+V.
    """
    raw_text = _get_highlighted_or_clipboard_text()
    if not raw_text:
        return "Sir, please highlight or copy the text you want me to work with first."

    # Build prompt
    system_instruction = (
        "You are J.A.R.V.I.S., Tony Stark's personal ghostwriter and editor.\n"
        "Your task is to transform the provided user text according to the requested instruction.\n"
        "CRITICAL RULES:\n"
        "1. Return ONLY the transformed text directly.\n"
        "2. Do NOT include any intro or conversational filler (e.g., 'Here is your rewritten text:').\n"
        "3. Maintain original intent, tone, and formatting where appropriate.\n"
    )

    task_prompts = {
        "professional": "Rewrite the following text into polished, professional, and clear executive English:\n\n",
        "grammar": "Correct all grammar, spelling, punctuation, and flow issues in the following text while preserving its original meaning:\n\n",
        "summarize": "Provide a concise, high-impact summary of the following text in 2 to 3 sentences:\n\n",
        "bullets": "Convert the following information into clean, high-impact bullet points:\n\n",
        "casual": "Rewrite the following text in a friendly, conversational, and natural tone:\n\n",
    }

    prefix = task_prompts.get(instruction_type, f"{custom_instruction}\n\n" if custom_instruction else task_prompts["professional"])
    full_prompt = f"{system_instruction}\n\nTask: {prefix}\"\"\"{raw_text}\"\"\""

    print("[GHOSTWRITER] Sending text to LLaMA 3.1:8b for refinement...")
    refined = ask_ai(full_prompt)
    if not refined or not refined.strip():
        return "I was unable to process the text with the neural brain, Sir."

    cleaned_result = refined.strip()
    # Strip any accidental wrapping quotes
    if cleaned_result.startswith('"""') and cleaned_result.endswith('"""'):
        cleaned_result = cleaned_result[3:-3].strip()
    elif cleaned_result.startswith('"') and cleaned_result.endswith('"'):
        cleaned_result = cleaned_result[1:-1].strip()

    # Place in clipboard
    pyperclip.copy(cleaned_result)

    if auto_paste:
        time.sleep(0.08)
        try:
            pyautogui.hotkey("ctrl", "v")
            play_fx("complete")
            return "Text polished and pasted in place, Sir."
        except Exception as paste_err:
            print(f"[GHOSTWRITER PASTE ERROR]: {paste_err}")
            play_fx("complete")
            return "Text refined and copied to your clipboard, Sir."

    play_fx("complete")
    return "Text refined and ready in your clipboard, Sir."
