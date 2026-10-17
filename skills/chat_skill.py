"""
Conversational Companion Skill for J.A.R.V.I.S.
Handles open-ended conversational prompts and chat mode through local LLaMA 3.1:8b.
"""

from voice_engine.sound_effects import play_fx
from ai_brain.ai_brain import ask_ai

skill = {
    "name": "Chat Companion",
    "priority": 50
}

CHAT_TRIGGERS = [
    "chat with me",
    "let's chat",
    "lets chat",
    "start chat",
    "talk to me",
    "can we talk"
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    return any(trigger in cmd for trigger in CHAT_TRIGGERS)


def execute(command: str) -> str:
    play_fx("wake")
    cmd = command.lower().strip()

    # If it's just the invitation to chat
    if any(cmd == trigger for trigger in CHAT_TRIGGERS):
        return "At your service, Sir. I am online and listening. What is on your mind?"

    # If there is substantive text beyond the trigger
    prompt = (
        "You are J.A.R.V.I.S., Tony Stark's personal AI assistant. "
        "Respond conversationally, thoughtfully, and in character with subtle British wit.\n\n"
        f"User: {command}"
    )
    play_fx("complete")
    return ask_ai(prompt)