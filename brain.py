import datetime
import webbrowser
from ai_brain import ask_ai
from internet_ai import search_internet


def process_command(command, memory, context):
    command = command.lower()

    # ===== SIMPLE CONTEXT PRONOUN HANDLING =====
    if any(word in command for word in [" he ", " she ", " him ", " her ", " they "]):
        if context.get("last_subject"):
            subject = context["last_subject"]
            command = command.replace(" he ", f" {subject} ")
            command = command.replace(" she ", f" {subject} ")
            command = command.replace(" him ", f" {subject} ")
            command = command.replace(" her ", f" {subject} ")
            command = command.replace(" they ", f" {subject} ")

    # ===== NEWS =====
    if "latest news" in command or "news" in command:
        return search_internet(command)

    # ===== NAME MEMORY =====
    elif "my name is" in command:
        name = command.replace("my name is", "").strip()
        memory["name"] = name
        return f"Nice to meet you {name}"

    elif "what is my name" in command:
        if "name" in memory:
            return f"Your name is {memory['name']}"
        else:
            return "I don't know your name yet."

    # ===== TIME =====
    elif "time" in command:
        now = datetime.datetime.now().strftime("%I:%M %p")
        return f"The time is {now}"

    # ===== OPEN YOUTUBE =====
    elif "open youtube" in command:
        webbrowser.open("https://youtube.com")
        return "Opening YouTube"

    # ===== CONTEXT SUBJECT STORAGE =====
    elif command.startswith("who is"):
        subject = command.replace("who is", "").strip()
        context["last_subject"] = subject
        return ask_ai(command, memory)

    # ===== AI FALLBACK =====
    return ask_ai(command, memory)