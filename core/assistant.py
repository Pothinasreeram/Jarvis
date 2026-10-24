from background_tasks import battery_monitor
import queue
import threading
import time
import os
import traceback
from ai_brain.personality import listening
WAKE_WORD = "jarvis"

# ---------------- GUI REFERENCES ----------------

app = None
set_status = None
update_display = None
# ============================================================
# JARVIS HUD STATE
# ============================================================

jarvis_state = "IDLE"


def set_jarvis_state(state):
    """
    Update the current JARVIS operating state.

    Possible states:
        IDLE
        LISTENING
        PROCESSING
        RESPONDING
        SPEAKING
    """
    global jarvis_state
    jarvis_state = state
    print(f"[JARVIS STATE] {state}")
thinking_animation = None

# ---------------- CORE IMPORTS ----------------
from voice_engine.voice import (
    speak,
    listen,
    speaking_status,
    is_interrupted,
    reset_interruption,
    stop_speaking
)


from system_layer.system_control import handle_system_commands

from command_system.command_splitter import split_commands
from command_system.automation import handle_automation
from command_system.intent_router import route_intent
import core.logger as logger
from core.lifecycle import shutdown_jarvis, register_shutdown_hook

from ai_brain.brain import process_command

from ai_brain.ai_brain import ask_ai, ask_ai_stream
from wake_word import listen_for_wake_word as local_wake_listen, trigger_wake_word


from memory_layer.memory import (
    save_memory,
    load_memory,
    remember_entity,
    get_current_entity,
    remember_entity_fact,
    recall_entity_fact
)

# ---------------- SKILL SYSTEM ----------------

from .skill_manager import (
    load_skills,
    execute_skill
)

pending_file_selection = None

# ---------------- BACKGROUND TASKS ----------------

from background_tasks.task_manager import (
    start_task,
    stop_task,
    list_tasks,
)
from background_tasks.notification_manager import (
    start_notification_manager,
)
from background_tasks.battery_monitor import (
    start_battery_monitor
)
from background_tasks.reminder_manager import (
    start_reminder_manager
)
from background_tasks.focus_guard import (
    start_focus_guard
)
from voice_engine.sound_effects import (
    play_fx,
    init_sound_fx
)

# ---------------- MEMORY ----------------

memory = load_memory()

conversation_context = {
    "last_subject": None,
    "last_command": None,
    "history": [],
    "conversation_active": False
}

last_subject = None
pending_action = None
thinking_active = False

# ============================================================
# V7.2.1 — COMMAND FEEDBACK
# ============================================================

def command_feedback(message, status="blue"):
    """
    Show Jarvis's current command-processing state.
    """

    print(
        f"[JARVIS STATUS] {message}"
    )

    if set_status:
        set_status(status)

    if app and update_display:
        app.after(
            0,
            update_display,
            message
        )

# ---------------- COMMAND QUEUE ----------------

command_queue = queue.Queue()

# ============================================================
# V7.2.3 — DUPLICATE COMMAND PROTECTION
# ============================================================

last_processed_command = ""
last_processed_command_time = 0.0

DUPLICATE_COMMAND_WINDOW = 3.0

# ---------------- COMMAND PROCESSOR ----------------

command_processor_running = False

# ============================================================
# V7.2.2 — SKILL-SPECIFIC FEEDBACK
# ============================================================

def skill_feedback(command):
    """
    Generate a visual status message based on the command.
    This is feedback only — Jarvis does NOT speak it.
    """

    text = command.lower().strip()

    feedback_map = [
        (["click"], "Locating UI element on screen..."),
        (["type", "write", "dictate"], "Dictating text to window..."),
        (["snap", "minimize", "maximize", "desktop"], "Managing windows..."),
        (["search", "look up", "news", "who won", "latest"], "Searching the live web..."),
        (["remember", "what do you remember", "forget"], "Accessing memory core..."),
        (["remind", "timer"], "Configuring reminder..."),
        (["chrome", "browser", "google"], "Opening Chrome..."),
        (["youtube"], "Searching YouTube..."),
        (["spotify", "music"], "Launching Spotify..."),
        (["weather", "temperature"], "Checking the weather..."),
        (["battery", "battery status"], "Checking battery status..."),
        (["file", "files", "document", "documents"], "Searching your files..."),
        (["focus", "pomodoro", "deep work"], "Configuring Focus Guard..."),
        (["voice", "piper", "bettany"], "Calibrating Neural Voice Engine..."),
        (["maid", "clean up", "organize"], "Executing Maid Protocol..."),
        (["protocol", "work mode", "gaming mode", "night mode", "stealth mode"], "Activating Protocol Sequence..."),
        (["rewrite", "ghostwriter", "grammar"], "Ghostwriter refining text..."),
        (["extract audio", "convert image", "summarize pdf", "convert video"], "Converting media..."),
        (["sentry", "lock workstation", "sentinel"], "Sentry Guard scanning environment..."),
        (["research", "deep research", "synthesize report"], "Autonomous Research Agent synthesizing intel..."),
        (["todo", "directive", "task", "directives"], "Stark Taskmaster updating directives..."),
        (["wellness", "posture", "hydration", "ergonomic"], "Consulting Wellness Protocol..."),
        (["diagnostic", "diagnostics", "hardware health", "mark vii", "mark 7"], "Executing Mark VII System Diagnostics..."),
        (["hacker news", "tech news", "headlines", "browse url", "summarize url"], "Navigating Live Web Intelligence..."),
        (["morning", "briefing", "brief me", "daily update"], "Compiling Executive Morning Briefing..."),
        (["voiceprint", "biometric", "calibrate voice", "enroll voice"], "Consulting Biometric Voiceprint Core..."),
        (["calculate", "calculator", "+", "-", "*", "/", "math"], "Calculating..."),
        (["camera"], "Opening camera..."),
        (["screenshot", "screen shot"], "Taking a screenshot..."),
        (["volume", "sound"], "Adjusting system volume..."),
        (["shutdown", "restart", "reboot"], "Preparing system operation..."),
    ]

    for keywords, message in feedback_map:
        if any(keyword in text for keyword in keywords):
            return message

    return "Executing skill..."

def is_recent_duplicate(command):
    """
    Prevent the same command from being processed twice
    within a very short window.
    """

    global last_processed_command
    global last_processed_command_time

    normalized = command.lower().strip()

    now = time.time()

    if (
        normalized == last_processed_command
        and (
            now - last_processed_command_time
            < DUPLICATE_COMMAND_WINDOW
        )
    ):
        print(
            "[V7.2.3] Duplicate command ignored:",
            normalized
        )

        return True

    return False

def process_queued_command(command):
    set_jarvis_state("PROCESSING")

    try:
        _process_queued_command(command)
    finally:
        set_jarvis_state("IDLE")


def _process_queued_command(command):
    global last_subject
    global pending_action
    global thinking_active
    global pending_file_selection

    try:
        print("\n" + "=" * 60)
        print(f"COMMAND : {command}")
        print("=" * 60)

        # ---------------- CLEAN COMMAND ----------------

        command = command.lower().strip()

        clean_command = command.replace(
            WAKE_WORD,
            ""
        ).strip()

        if not clean_command:
            print("Wake word only.")
            return

        # ---------------- CONVERSATION EXIT ----------------

        exit_commands = [
            "sleep",
            "stop listening",
            "goodbye",
            "shutdown conversation",
            "go idle",
            "go to sleep"
        ]

        if clean_command in exit_commands:

            reply = "Going into standby mode, sir."

            command_feedback(reply)
            speak(reply)

            conversation_context["conversation_active"] = False

            return

        # ---------------- FILE SELECTION ----------------

        if pending_file_selection:

            if clean_command.startswith("number"):

                try:
                    number = int(
                        clean_command.split()[-1]
                    )

                    if 1 <= number <= len(
                        pending_file_selection
                    ):

                        from system_layer.file_search_controller import open_match

                        match = pending_file_selection[
                            number - 1
                        ]

                        reply = open_match(match)

                        pending_file_selection = None

                        command_feedback(reply)

                        speak(reply)

                        return

                except Exception as e:
                    print("[FILE SELECTION ERROR]", e)

        # ---------------- BACKGROUND TASKS ----------------

        # Start battery monitor
        if "start battery monitor" in clean_command:

            reply = start_task(
                "battery_monitor",
                battery_monitor
            )

            command_feedback(
                "Battery monitoring activated.",
                "green"
            )

            speak(
                "Battery monitoring is now active."
            )

            return

        # Stop battery monitor
        if "stop battery monitor" in clean_command:

            reply = stop_task(
                "battery_monitor"
            )

            command_feedback(
                "Battery monitoring stopped.",
                "green"
            )

            speak(
                "Battery monitoring has been stopped."
            )

            return

        # List background tasks
        if (
            "list background tasks" in clean_command
            or "show background tasks" in clean_command
            or "what background tasks are running" in clean_command
        ):

            tasks = list_tasks()

            if tasks:

                task_names = ", ".join(tasks)

                reply = (
                    f"Currently running background tasks: "
                    f"{task_names}."
                )

            else:

                reply = "There are no background tasks running."

            command_feedback(
                reply,
                "blue"
            )

            speak(reply)

            return

        # ---------------- CONFIRMATION ----------------

        if pending_action:

            if clean_command in [
                "yes",
                "confirm",
                "do it"
            ]:

                # ----- SHUTDOWN -----

                if pending_action == "shutdown":

                    speak(
                        "Shutting down system."
                    )

                    os.system(
                        "shutdown /s /t 1"
                    )


                # ----- RESTART -----

                elif pending_action == "restart":

                    speak(
                        "Restarting system."
                    )

                    os.system(
                        "shutdown /r /t 1"
                    )


                # ----- WINDOWS SLEEP -----

                elif pending_action == "windows_sleep":

                    speak(
                        "Putting the computer to sleep."
                    )

                    os.system(
                        "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"
                    )


                elif isinstance(pending_action, tuple) and pending_action[0] == "destructive":
                    actual_command = pending_action[1]
                    pending_action = None
                    clean_command = actual_command
                    # Fall through to execute actual_command below

                else:
                    pending_action = None
                    return

            elif clean_command in [
                "no",
                "cancel",
                "abort",
                "stop"
            ]:

                speak(
                    "Action cancelled. All files and systems remain untouched, Sir."
                )

                pending_action = None

                return

        # ---------------- DESTRUCTIVE ACTION SECURITY GUARD ----------------

        destructive_triggers = [
            "delete file",
            "delete folder",
            "delete files",
            "delete my",
            "remove folder",
            "format drive",
            "format disk",
            "wipe drive"
        ]

        if any(trig in clean_command for trig in destructive_triggers):
            pending_action = ("destructive", clean_command)
            warn_reply = (
                "Sir, that command is destructive. Are you certain you want me to proceed?"
            )
            command_feedback(warn_reply, status="yellow")
            speak(warn_reply)
            return

        # ---------------- PROCESSING ----------------

        command_feedback(
            "Processing command...",
            "blue"
        )

        play_fx("ack")
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

            command_feedback(automation_reply, status="green")

            

            speak(automation_reply)

            return

        # ---------------- MULTI COMMANDS ----------------

        commands = split_commands(
            clean_command
        )

        for single_command in commands:

            clean_command = single_command.strip()

            print(
                "\n[PROCESSING COMMAND]:",
                clean_command
            )

            # ---------------- SKILL SYSTEM ----------------

            command_feedback(
                skill_feedback(clean_command),
                "blue"
            )

            print(
                "Before execute_skill:",
                clean_command
            )

            skill_reply = execute_skill(
                clean_command
            )

            if isinstance(
                skill_reply,
                dict
            ):

                if skill_reply["type"] == "file_selection":

                    pending_file_selection = (
                        skill_reply["matches"]
                    )

                    speak(
                        skill_reply["message"]
                    )

                    continue

            print(
                "[SKILL RESULT] ->",
                skill_reply
            )

            # ---------------- SKILL SUCCESS ----------------

            if skill_reply:

                thinking_active = False

                command_feedback(skill_reply, status="green")
                play_fx("complete")

                speak(skill_reply)

                continue

            # ---------------- INTENT ROUTING ----------------

            intent = route_intent(
                clean_command
            )

            print(
                "[INTENT] ->",
                intent
            )

            # ---------------- SYSTEM ----------------

            if intent == "system":

                # ----- SHUTDOWN -----

                if "shutdown" in clean_command:

                    pending_action = "shutdown"

                    reply = (
                        "Sir, are you sure you "
                        "want to shut down the system?"
                    )

                    thinking_active = False

                    command_feedback(
                        reply,
                        status="green"
                    )

                    speak(reply)

                    return


                # ----- RESTART / REBOOT -----

                elif (
                    "restart" in clean_command
                    or "reboot" in clean_command
                ):

                    pending_action = "restart"

                    reply = (
                        "Sir, are you sure you "
                        "want to restart the system?"
                    )

                    thinking_active = False

                    command_feedback(
                        reply,
                        status="green"
                    )

                    speak(reply)

                    return


                # ----- WINDOWS SLEEP -----
    # IMPORTANT:
    # Do NOT use plain "sleep" here because
    # "sleep" is already Jarvis conversation standby.

                elif (
                    "sleep computer" in clean_command
                    or "sleep the computer" in clean_command
                    or "sleep my computer" in clean_command
                    or "sleep pc" in clean_command
                    or "sleep the pc" in clean_command
                    or "sleep my pc" in clean_command
                    or "put computer to sleep" in clean_command
                    or "put my computer to sleep" in clean_command
                    or "put pc to sleep" in clean_command
                    or "put my pc to sleep" in clean_command
                ):

                    pending_action = "windows_sleep"

                    reply = (
                        "Sir, are you sure you "
                        "want to put the computer to sleep?"
                    )

                    thinking_active = False

                    command_feedback(
                        reply,
                        status="green"
                    )

                    speak(reply)

                    return

            # ---------------- CONTEXT ENGINE ----------------

            words = clean_command.split()

            # save previous command
            conversation_context["last_command"] = clean_command

            conversation_context["conversation_active"] = True

            #store conversation history
            conversation_context["history"].append(
                clean_command
            )

            # Limit memory size
            if len(conversation_context["history"]) > 10:
                conversation_context["history"].pop(0)

            # Detect main subject

            subject = None

            if len(words) >= 3:

                # who is Elon Musk
                if words[0] == "who" and words[1] == "is":

                    subject = " ".join(words[2:])


                # tell me about Elon Musk
                elif words[0] in ["tell", "explain"]:

                    if "about" in words:
                        index = words.index("about")
                        subject = " ".join(words[index + 1:])


                # what is Elon Musk net worth
                elif words[0] == "what":

                    ignored = [
                        "what",
                        "is",
                        "are",
                        "was",
                        "were"
                    ]

                    possible = [
                        w for w in words[1:]
                        if w not in [
                            "his",
                            "her",
                            "their",
                            "its"
                        ]
                    ]
                

                    if len(possible) > 1:
                        subject = " ".join(possible)

            if subject:

                # Do not overwrite context with pronoun questions
                if not any(
                    p in words
                    for p in [
                        " he ",
                        " she ",
                        " him ",
                        " her ",
                        " they "
                    ]
                ): 
                    conversation_context["last_subject"] = subject

            last_subject = conversation_context.get(
                "last_subject"
            )


            # Pronoun replacement

            if last_subject:

                # ---------------- CONTEXT RESOLUTION ----------------

                pronouns = [
                    "he",
                    "she",
                    "him",
                    "her",
                    "they",
                    "his",
                    "their"
                ]


                if last_subject:

                    for p in pronouns:

                        if p in words:

                            clean_command = clean_command.replace(
                                p,
                                last_subject
                            )

                            print(
                                "[CONTEXT RESOLVED]:",
                                clean_command
                            )

                            break
                      
            # ---------------- BRAIN ----------------

            command_feedback(
                "Thinking...",
                "blue"
            )

            reply = process_command(
                clean_command,
                memory,
                conversation_context
            )

            print(
                "[BRAIN] ->",
                reply
            )

            # ---------------- AI FALLBACK ----------------

            if not reply:

                command_feedback(
                    "Thinking...",
                    "blue"
                )
                set_jarvis_state("PROCESSING")

                # Save conversation context for AI
                memory["last_subject"] = conversation_context.get(
                    "last_subject",
                    ""
                )

                memory["history"] = conversation_context.get(
                    "history",
                    []
                )

                memory["last_command"] = conversation_context.get(
                    "last_command",
                    ""
                )

                reset_interruption()
                sentences_received = []
                first_sentence = True

                for sentence in ask_ai_stream(clean_command, memory):
                    if not sentence.strip():
                        continue
                    if is_interrupted():
                        print("[BARGE-IN] Stream aborted due to interruption.")
                        break

                    sentences_received.append(sentence)

                    if first_sentence:
                        first_sentence = False
                        thinking_active = False
                        command_feedback(
                            "Responding...",
                            "green"
                        )

                    # Update display with accumulated text so the user reads in real-time
                    current_display_text = " ".join(sentences_received)
                    app.after(
                        0,
                        update_display,
                        current_display_text
                    )

                    # Speak this sentence immediately while next sentence is generating!
                    set_jarvis_state("SPEAKING")
                    try:
                        speak(sentence)
                    finally:
                        set_jarvis_state("PROCESSING")

                    if is_interrupted():
                        print("[BARGE-IN] Speech playback halted by user.")
                        break


                thinking_active = False

                if sentences_received:
                    try:
                        from memory_layer.sqlite_memory import log_conversation
                        log_conversation(clean_command, " ".join(sentences_received), intent="ai_brain")
                    except Exception:
                        pass

                if is_interrupted():
                    app.after(
                        0,
                        update_display,
                        "[INTERRUPTED] Listening..."
                    )
                    command_feedback("Interrupted", "yellow")
                    set_jarvis_state("LISTENING")
                elif not sentences_received:
                    fallback_reply = (
                        "I am not sure how to respond to that."
                    )
                    app.after(
                        0,
                        update_display,
                        fallback_reply
                    )
                    set_jarvis_state("SPEAKING")
                    try:
                        speak(fallback_reply)
                    finally:
                        set_jarvis_state("PROCESSING")

                save_memory(memory)
                if not is_interrupted():
                    set_jarvis_state("IDLE")
                    time.sleep(0.5)
                    command_feedback("Ready", "idle")

            else:
                thinking_active = False
                save_memory(memory)
                reset_interruption()

                # ---------------- DIRECT COMMAND RESPONSE ----------------

                command_feedback(
                    "Responding...",
                    "green"
                )
                set_jarvis_state("RESPONDING")
                app.after(
                    0,
                    update_display,
                    reply
                )

                try:
                    from memory_layer.sqlite_memory import log_conversation
                    log_conversation(sub_cmd, reply, intent="skill")
                except Exception:
                    pass

                set_jarvis_state("SPEAKING")

                try:
                    speak(reply)
                finally:
                    set_jarvis_state("PROCESSING")

                if is_interrupted():
                    app.after(
                        0,
                        update_display,
                        "[INTERRUPTED] Listening..."
                    )
                    command_feedback("Interrupted", "yellow")
                    set_jarvis_state("LISTENING")
                else:
                    time.sleep(0.5)
                    command_feedback(
                        "ready",
                        "idle"
                    )



    except Exception:

        traceback.print_exc()

        thinking_active = False

        command_feedback("Idle", status="gray")

# ---------------- COMMAND WORKER ----------------

def command_worker():
    global command_processor_running

    command_processor_running = True

    print("[COMMAND WORKER] Started")

    while True:

        command = command_queue.get()

        try:

            if command is None:
                continue

            print(
                "[QUEUE COMMAND]:",
                command
            )

            process_queued_command(
                command
            )

        except Exception:

            print(
                "[WORKER ERROR]"
            )

            traceback.print_exc()

        finally:

            command_queue.task_done()
# ---------------- HELPER FUNCTIONS ----------------
def listen_for_wake_word(timeout=5.0):
    """Listen for the wake word using zero-latency local ONNX engine."""
    set_jarvis_state("LISTENING")

    try:
        return local_wake_listen(timeout=timeout)
    except Exception as e:
        print("[WAKE ERROR]:", e)
        time.sleep(0.5)
        return False
    finally:
        set_jarvis_state("IDLE")


# ============================================================
# V7.2.3 — DUPLICATE COMMAND PROTECTION
# ============================================================

LAST_PROCESSED_COMMAND = ""
LAST_PROCESSED_TIME = 0.0

DUPLICATE_COMMAND_WINDOW = 4.0


def is_duplicate_command(command):
    """
    Prevent the same voice command from being executed
    repeatedly within a short time window.
    """

    global LAST_PROCESSED_COMMAND
    global LAST_PROCESSED_TIME

    normalized = command.lower().strip()

    now = time.time()

    if (
        normalized == LAST_PROCESSED_COMMAND
        and now - LAST_PROCESSED_TIME < DUPLICATE_COMMAND_WINDOW
    ):
        print(
            "[V7.2.3] Duplicate command ignored:",
            normalized
        )

        return True

    LAST_PROCESSED_COMMAND = normalized
    LAST_PROCESSED_TIME = now

    return False




# ---------------- WATCHDOG ----------------

def system_watchdog():

    while True:

        time.sleep(5)

# ---------------- COMMAND PROCESSOR ----------------

# ---------------- MAIN LOOP ----------------

def jarvis_loop():
    global thinking_active

    global last_processed_command
    global last_processed_command_time

    # ---------------- V7.0 SMART CONVERSATION SETTINGS ----------------

    WAKE_WORD_TIMEOUT = 5
    INITIAL_COMMAND_TIMEOUT = 8
    FOLLOW_UP_TIMEOUT = 10

    while True:

        try:

            set_status("yellow")
            set_jarvis_state("IDLE")

            # ============================================================
            # WAIT FOR WAKE WORD (LOCAL ZERO-LATENCY ONNX ENGINE)
            # ============================================================

            print("Waiting for wake word ('Jarvis')...")

            if not listen_for_wake_word(timeout=WAKE_WORD_TIMEOUT):
                continue

            print(
                "Wake word detected. "
                "Entering conversation mode."
            )
            play_fx("wake")


            # ================================================
            # V7.1.2 PERSONALITY - WAKE RESPONSE
            # ================================================

            wake_response = listening()

            print(
                "[PERSONALITY]:",
                wake_response
            )

            speak(wake_response)

            conversation_context[
                "conversation_active"
            ] = True

            # ============================================================
            # CONVERSATION MODE
            # ============================================================

            while conversation_context[
                "conversation_active"
            ]:

                # --------------------------------------------------------
                # LISTEN FOR COMMAND
                # --------------------------------------------------------

                print(
                    "[V7.0] Listening for command..."
                )

                command = listen(
                    timeout=INITIAL_COMMAND_TIMEOUT,
                    phrase_time_limit=8
                )

                # --------------------------------------------------------
                # NO COMMAND
                # --------------------------------------------------------

                if not command:

                    print(
                        "[V7.0] No command detected."
                    )

                    print(
                        "[V7.0] Returning to standby."
                    )

                    conversation_context[
                        "conversation_active"
                    ] = False

                    break

                # --------------------------------------------------------
                # INTERRUPT DETECTION
                # --------------------------------------------------------

                if (
                    speaking_status()
                    and WAKE_WORD.lower()
                    in command.lower()
                ):

                    print(
                        "[V7.0] Interrupt detected."
                    )

                    continue

                # --------------------------------------------------------
                # CLEAN COMMAND
                # --------------------------------------------------------

                command = command.lower().strip()

                clean_command = command.replace(
                    WAKE_WORD.lower(),
                    ""
                ).strip()

                # --------------------------------------------------------
                # WAKE WORD ONLY
                # --------------------------------------------------------

                if not clean_command:

                    print(
                        "[V7.0] Wake word repeated."
                    )

                    continue

                print(
                    "[CLEAN COMMAND]:",
                    clean_command
                )

                #=======================================================
                # v7.2.3 — DUPLICATE COMMAND PROTECTION
                #=======================================================
                if is_recent_duplicate(clean_command):

                    print(
                        "[V7.2.3] command skipped."
                    )

                    continue

                #=======================================================
                # RECORD COMMAND BEFORE QUEUEING
                #=======================================================

                last_processed_command = clean_command
                last_processed_command_time = time.time()

                # ========================================================
                # SEND COMMAND TO QUEUE
                # ========================================================

                command_queue.put(
                    clean_command
                )

                print(
                    "[VOICE -> QUEUE]:",
                    clean_command
                )

                # ========================================================
                # WAIT FOR PROCESSING + TTS
                # ========================================================

                print(
                    "[VOICE] Waiting for command "
                    "processing to finish..."
                )

                command_queue.join()

                print(
                    "[VOICE] Command processing finished."
                )

                # ========================================================
                # V7.0 FOLLOW-UP WINDOW
                # ========================================================

                if not conversation_context[
                    "conversation_active"
                ]:
                    print(
                        "[V7.0] Conversation ended by command."
                    )
                    break

                print(
                    "[V7.0] Waiting for follow-up..."
                )

                follow_up = listen(
                    timeout=FOLLOW_UP_TIMEOUT,
                    phrase_time_limit=8
                )

                # ========================================================
                # FOLLOW-UP TIMEOUT
                # ========================================================

                if not follow_up:

                    print(
                        "[V7.0] No follow-up detected."
                    )

                    print(
                        "[V7.0] Conversation ended."
                    )
                    play_fx("standby")

                    conversation_context[
                        "conversation_active"
                    ] = False

                    set_status("yellow")

                    break

                # ========================================================
                # FOLLOW-UP RECEIVED
                # ========================================================

                print(
                    "[V7.0] Follow-up detected:",
                    follow_up
                )

                follow_up = follow_up.lower().strip()

                clean_follow_up = follow_up.replace(
                    WAKE_WORD.lower(),
                    ""
                ).strip()

                # --------------------------------------------------------
                # WAKE WORD ONLY
                # --------------------------------------------------------

                if not clean_follow_up:

                    print(
                        "[V7.0] Wake word repeated."
                    )

                    continue

                print(
                    "[V7.0] Follow-up -> Queue:",
                    clean_follow_up
                )

                # ========================================================
                # QUEUE FOLLOW-UP
                # ========================================================

                command_queue.put(
                    clean_follow_up
                )

                print(
                    "[V7.0] Waiting for follow-up "
                    "processing..."
                )

                command_queue.join()

                print(
                    "[V7.0] Follow-up processing finished."
                )

                # ========================================================
                # LOOP CONTINUES
                # ========================================================

                if not conversation_context[
                    "conversation_active"
                ]:
                    print(
                        "[V7.0] Conversation ended."
                    )
                    break

                print(
                    "[V7.0] Listening for another "
                    "follow-up..."
                )

        except Exception:

            print(
                "\n===== MAIN LOOP ERROR ====="
            )

            traceback.print_exc()

            conversation_context[
                "conversation_active"
            ] = False

            time.sleep(1)

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

    # START NOTIFICATION MANAGER

    notification_status = start_notification_manager()

    print(
        "[NOTIFICATION MANAGER] Status:",
        notification_status
    )

    # START PROACTIVE SERVICES (BATTERY MONITOR, REMINDERS, FOCUS GUARD & SOUND FX)

    try:
        init_sound_fx()
        start_battery_monitor()
        start_reminder_manager()
        start_focus_guard()
        try:
            from background_tasks.wellness_monitor import start_wellness_monitor
            start_wellness_monitor(speak_callback=speak)
        except Exception:
            pass
        try:
            from background_tasks.sentry_guard import start_sentry_service
            start_sentry_service()
        except Exception:
            pass
        print("[PROACTIVE INTELLIGENCE] Battery, reminder, Focus Guard, Wellness, and Sentry services active.")
    except Exception as proactive_err:
        print("[PROACTIVE SERVICE ERROR]:", proactive_err)

    # START COMMAND WORKER

    threading.Thread(
        target=command_worker,
        daemon=True
    ).start()

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