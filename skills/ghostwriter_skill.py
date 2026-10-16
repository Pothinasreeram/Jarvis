"""
Ghostwriter Voice Skill for J.A.R.V.I.S.
Handles voice requests to rewrite, correct grammar, summarize, translate,
or reformat highlighted on-screen text in any active window.
"""

import re
from system_layer.ghostwriter_controller import process_ghostwriter_task

skill = {
    "name": "Ghostwriter Skill",
    "priority": 22,
}

TRIGGER_KEYWORDS = [
    "rewrite this",
    "rewrite professionally",
    "rewrite my text",
    "rewrite selection",
    "fix grammar",
    "correct grammar",
    "fix the grammar",
    "summarize this",
    "summarize selection",
    "summarize what i selected",
    "bullet points",
    "convert to bullets",
    "make this casual",
    "make this friendly",
    "ghostwriter",
    "translate this",
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if any(action in cmd for action in ["rewrite", "grammar", "summarize", "ghostwriter"]) and any(target in cmd for target in ["this", "text", "selection", "clipboard"]):
        return True
    if "translate this to" in cmd:
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # 1. Translation
    if "translate" in cmd:
        match = re.search(r'translate\s+(?:this\s+)?to\s+([a-zA-Z]+)', cmd)
        lang = match.group(1).capitalize() if match else "English"
        custom_prompt = f"Translate the following text accurately and naturally into {lang}:\n\n"
        return process_ghostwriter_task("custom", custom_instruction=custom_prompt)

    # 2. Grammar correction
    if "grammar" in cmd or "spelling" in cmd:
        return process_ghostwriter_task("grammar")

    # 3. Summarization
    if "summarize" in cmd or "summary" in cmd:
        return process_ghostwriter_task("summarize")

    # 4. Bullet points
    if "bullet" in cmd:
        return process_ghostwriter_task("bullets")

    # 5. Casual / Friendly
    if "casual" in cmd or "friendly" in cmd:
        return process_ghostwriter_task("casual")

    # 6. Professional rewrite (default)
    return process_ghostwriter_task("professional")
