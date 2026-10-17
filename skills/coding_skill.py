"""
Developer AI & Code Copilot Skill for J.A.R.V.I.S.
Generates, debugs, and explains code using local LLaMA 3.1:8b,
and saves scripts directly to the user's Desktop.
"""

import os
import re
from voice_engine.sound_effects import play_fx
from ai_brain.ai_brain import ask_ai

skill = {
    "name": "Coding Copilot",
    "priority": 20
}

TRIGGER_PREFIXES = [
    "write code to ",
    "write code for ",
    "generate code for ",
    "generate code to ",
    "write a script to ",
    "write a python script to ",
    "write python code to ",
    "code a ",
    "code an ",
    "write a function to ",
    "create a function to "
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(cmd.startswith(p) for p in TRIGGER_PREFIXES):
        return True
    if any(w in cmd for w in ["write code", "generate code", "write a script", "write python script"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()
    play_fx("wake")

    # Extract user's coding directive
    prompt_topic = cmd
    for p in TRIGGER_PREFIXES:
        if cmd.startswith(p):
            prompt_topic = cmd[len(p):].strip()
            break

    system_prompt = (
        "You are J.A.R.V.I.S., Tony Stark's expert software engineering intelligence. "
        "Write clean, elegant, production-ready code for the requested task. "
        "Include concise docstrings, inline comments, and best practices. "
        "Format the code clearly inside a markdown code block.\n\n"
        f"Coding Task: {prompt_topic}"
    )

    play_fx("complete")
    code_result = ask_ai(system_prompt)

    # Save to user Desktop
    desktop_path = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
    if not os.path.exists(desktop_path):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    out_file = os.path.join(desktop_path, "Generated_Code.py")
    try:
        # Extract code inside backticks if available
        code_match = re.search(r'```(?:python)?\s*(.*?)\s*```', code_result, re.DOTALL)
        content_to_save = code_match.group(1) if code_match else code_result

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(content_to_save)

        return f"Code for '{prompt_topic}' generated and saved to your Desktop as Generated_Code.py, Sir."
    except Exception as e:
        print(f"[CODING SKILL FILE SAVE ERROR]: {e}")
        return code_result