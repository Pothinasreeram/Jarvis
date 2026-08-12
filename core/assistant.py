import threading
import time
import os
import traceback
WAKE_WORD = "jarvis"

# ---------------- GUI REFERENCES ----------------

app = None
set_status = None
update_display = None
thinking_animation = None

# ---------------- CORE IMPORTS ----------------
from voice_engine.voice import (
    speak,
    listen,
    speaking_status
)

from system_layer.system_control import handle_system_commands

from command_system.intent_router import route_intent

from ai_brain.brain import process_command

from ai_brain.internet_ai import ask_ai


from memory_layer.memory import (
    save_memory,
    load_memory
)

# ---------------- SKILL SYSTEM ----------------

from .skill_manager import (
    load_skills,
    execute_skill
)

pending_file_selection = None

# ---------------- BACKGROUND TASKS ----------------

from background_tasks.task_manager import start_task

from background_tasks.battery_monitor import (
    battery_monitor
)

# ---------------- MEMORY ----------------

memory = load_memory()

conversation_context = {
    "last_subject": None
}

last_subject = None
pending_action = None
thinking_active = False

# ---------------- HELPER FUNCTIONS ----------------

def listen_for_wake_word():
    """Listen for the wake word."""
    command = listen()
    return command and WAKE_WORD.lower() in command.lower()


def handle_automation(command):
    """Handle automation commands."""
    return None

def split_commands(command):
    """Split multiple commands separated by 'and' or similar."""
    return [command]

# ---------------- WATCHDOG ----------------

def system_watchdog():

    while True:

        time.sleep(5)

# ---------------- MAIN LOOP ----------------

def jarvis_loop():

    global last_subject
    global pending_action
    global thinking_active
    global pending_file_selection

    while True:

        try:

            set_status("yellow")

            # WAIT FOR WAKE WORD
            print("Waiting for wake word...")
            if not listen_for_wake_word():
                continue

            print("Wake word detected. Entering conversation mode.")

            CONVERSATION_TIMEOUT = 30
            last_active_time = time.time()

            while True:

                if time.time() - last_active_time > CONVERSATION_TIMEOUT:
                    print("Conversation timed out.")
                    break

                command = listen()

                if not command:
                    time.sleep(0.2)
                    continue

                last_active_time = time.time()

                # INTERRUPT SPEECH

                if speaking_status() and WAKE_WORD in command.lower():

                    print("Interrupt detected.")

                    continue

                command = command.lower()

                clean_command = command.replace(
                    WAKE_WORD,
                    ""
                ).strip()
                if clean_command == "":
                    print("Wake word repeated.")
                    continue

                

                if not clean_command:
                    continue

                # ---------------- FILE SELECTION HANDLER ----------------

                if pending_file_selection:

                    if clean_command.startswith("number"):
                        try:
                            number = int(
                                clean_command.split()[-1]
                            )

                            if 1 <= number <= len(pending_file_selection):
                                from system_layer.file_search_controller import open_match

                                match = pending_file_selection[number - 1]

                                reply = open_match(match)

                                pending_file_selection = None

                                speak(reply)

                                continue

                        except Exception as e:
                            print(e)

                # ---------------- BATTERY MONITOR ----------------

                if "start battery monitor" in clean_command:

                    reply = start_task(
                        "battery_monitor",
                        battery_monitor
                    )

                    app.after(
                        0,
                        update_display,
                        reply
                    )

                    speak(reply)

                    continue

                # ---------------- CONFIRMATION HANDLER ----------------

                if pending_action:

                    if clean_command in [
                        "yes",
                        "confirm",
                        "do it"
                    ]:

                        if pending_action == "shutdown":

                            speak("Shutting down system.")

                            os.system("shutdown /s /t 1")

                        pending_action = None

                        continue

                    elif clean_command in [
                        "no",
                        "cancel"
                    ]:

                        speak("Action cancelled.")

                        pending_action = None

                        continue

                # ---------------- PROCESSING ----------------

                set_status("blue")

                thinking_active = True

                app.after(
                    0,
                    thinking_animation
                )

                # ---------------- AUTOMATION ----------------

                automation_reply = handle_automation(
                    clean_command
                )

                if automation_reply:

                    thinking_active = False

                    set_status("green")

                    app.after(
                        0,
                        update_display,
                        automation_reply
                    )

                    speak(automation_reply)

                    time.sleep(1.0)

                    set_status("idle")

                    continue

                # ---------------- MULTI COMMANDS ----------------

                commands = split_commands(clean_command)

                for single_command in commands:

                    clean_command = single_command.strip()

                    print("\n" + "=" * 60)
                    print(f"COMMAND : {clean_command}")
                    print("=" * 60)

                    # ---------------- SKILL SYSTEM ----------------
                    print("Before execute_skill:", clean_command)

                    skill_reply = execute_skill(clean_command) 
                    if isinstance(skill_reply, dict):

                        if skill_reply["type"] == "file_selection":

                            pending_file_selection = skill_reply["matches"]

                            speak(skill_reply["message"])

                            continue

                    print(f"[SKILL RESULT] -> {skill_reply}")

                    print("Skill returned:", skill_reply)

                    if skill_reply:

                        print("Executing skill response")

                        thinking_active = False

                        set_status("green")

                        app.after(0, update_display, skill_reply)

                        speak(skill_reply)

                        time.sleep(1.0)

                        set_status("idle")

                        continue

                    # ---------------- INTENT ROUTING ----------------

                    # determine intent from the cleaned command
                    intent = route_intent(clean_command)

                    print(f"[INTENT] -> {intent}")

                    print("DEBUG intent:", intent)
                    # ---------------- SYSTEM ----------------

                    if intent == "system":

                        if "shutdown" in clean_command:

                            pending_action = "shutdown"

                            reply = (
                                "Sir, are you sure you "
                                "want to shut down the system?"
                            )

                            thinking_active = False

                            set_status("green")

                            app.after(
                                0,
                                update_display,
                                reply
                            )

                            speak(reply)

                            time.sleep(1.0)

                            set_status("idle")

                            continue

                    # ---------------- CONTEXT HANDLING ----------------

                    words = clean_command.split()

                    if len(words) >= 2:

                        if words[0] in [
                            "who",
                            "what"
                        ]:

                            last_subject = " ".join(
                                words[2:]
                            )

                        elif words[0] in [
                            "tell",
                            "explain"
                        ]:

                            last_subject = " ".join(
                                words[3:]
                            )

                        elif len(words) == 2:

                            last_subject = clean_command

                    if last_subject:

                        pronouns = [
                            " he ",
                            " she ",
                            " him ",
                            " her ",
                            " they "
                        ]

                        for pronoun in pronouns:

                            if pronoun in f" {clean_command} ":

                                clean_command = clean_command.replace(
                                    pronoun.strip(),
                                    last_subject
                                )

                    # ---------------- BRAIN ----------------

                    reply = process_command(
                        clean_command,
                        memory,
                        conversation_context
                    )
                    print(f"[BRAIN] -> {reply}")
                    # ---------------- AI FALLBACK ----------------

                    if not reply or reply == "":

                        reply = ask_ai(
                            clean_command,
                            memory
                        )
                        print(f"[AI] -> {reply}")
                    thinking_active = False

                    if not reply:

                        reply = (
                            "I am not sure how "
                            "to respond to that."
                        )

                    save_memory(memory)

                    # ---------------- SPEAKING ----------------

                    set_status("green")

                    app.after(
                        0,
                        update_display,
                        reply
                    )

                    speak(reply)

                    time.sleep(1.0)

                    set_status("idle")

        except Exception as e:

            print("\n===== FULL ERROR =====")
            traceback.print_exc()
            print("=====================\n")
            thinking_active = False

            set_status("idle")

# ---------------- START ASSISTANT ----------------

def start_jarvis(
    gui_app,
    gui_status,
    gui_display,
    gui_thinking_animation
):

    global app
    global set_status
    global update_display
    global thinking_animation

    app = gui_app

    set_status = gui_status

    update_display = gui_display

    thinking_animation = gui_thinking_animation

    # LOAD SKILLS

    load_skills()

    # START MAIN LOOP

    threading.Thread(
        target=jarvis_loop,
        daemon=True
    ).start()

    # START WATCHDOG

    threading.Thread(
        target=system_watchdog,
        daemon=True
    ).start()