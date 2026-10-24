"""
JARVIS Proactive Reminder & Timer Manager
Allows setting timers and spoken reminders that fire accurately in the background.
"""

import time
import threading
import re
from typing import List, Dict, Optional
from background_tasks.notification_manager import send_notification

_reminders: List[Dict] = []
_lock = threading.Lock()
_counter = 1
_reminder_thread = None
_running = False


def add_reminder(seconds: float, message: str) -> Dict:
    """Add a new scheduled reminder."""
    global _counter
    due_timestamp = time.time() + max(1.0, seconds)

    with _lock:
        rem_id = _counter
        _counter += 1
        reminder_item = {
            "id": rem_id,
            "due_time": due_timestamp,
            "message": message.strip(),
            "duration_sec": seconds
        }
        _reminders.append(reminder_item)

    print(f"[REMINDER ADDED] ID {rem_id}: in {seconds}s -> '{message}'")
    return reminder_item


def get_active_reminders() -> List[Dict]:
    """Return all currently pending reminders."""
    now = time.time()
    with _lock:
        return [
            {
                "id": r["id"],
                "message": r["message"],
                "seconds_left": max(0, int(r["due_time"] - now))
            }
            for r in _reminders
        ]


def cancel_reminder(reminder_id: int) -> bool:
    """Cancel a pending reminder by ID."""
    global _reminders
    with _lock:
        initial_len = len(_reminders)
        _reminders = [r for r in _reminders if r["id"] != reminder_id]
        return len(_reminders) < initial_len


def _reminder_worker(stop_event: Optional[threading.Event] = None):
    """Background worker that checks and fires due reminders."""
    global _reminders, _running
    print("[REMINDER WORKER] Started.")

    while _running:
        if stop_event is not None and stop_event.is_set():
            break

        now = time.time()
        due_list = []

        with _lock:
            remaining = []
            for r in _reminders:
                if r["due_time"] <= now:
                    due_list.append(r)
                else:
                    remaining.append(r)
            _reminders = remaining

        for due in due_list:
            msg = due["message"]
            print(f"[REMINDER TRIGGERED]: {msg}")
            spoken_alert = f"Sir, this is your reminder: {msg}."
            try:
                send_notification(spoken_alert)
            except Exception as e:
                print(f"[REMINDER ALERT ERROR]: {e}")

        # Sleep in small increments for prompt shutdown
        for _ in range(10):
            if not _running or (stop_event and stop_event.is_set()):
                break
            time.sleep(0.1)

    print("[REMINDER WORKER] Stopped.")


def start_reminder_manager(stop_event: Optional[threading.Event] = None):
    """Start the reminder background manager thread."""
    global _reminder_thread, _running
    if _reminder_thread and _reminder_thread.is_alive():
        return "Reminder manager already running."

    _running = True
    _reminder_thread = threading.Thread(
        target=_reminder_worker,
        args=(stop_event,),
        name="Jarvis-Reminder-Worker",
        daemon=True
    )
    _reminder_thread.start()
    return "Reminder manager started."


def stop_reminder_manager():
    """Stop the reminder background worker."""
    global _running
    _running = False


def parse_reminder_phrase(text: str) -> Optional[Dict]:
    """
    Parse a reminder command into seconds and message.
    Examples:
      - "remind me in 5 minutes to call John" -> {'seconds': 300, 'message': 'call John'}
      - "remind me in 30 seconds to check the stove" -> {'seconds': 30, 'message': 'check the stove'}
      - "set a timer for 10 minutes" -> {'seconds': 600, 'message': 'Your 10 minute timer is up'}
      - "remind me in 1 hour to take a break" -> {'seconds': 3600, 'message': 'take a break'}
    """
    cleaned = text.strip().lower()

    # Pattern 1: remind me in X (seconds|minutes|hours) (to|that|about) Y
    match = re.search(
        r"remind\s+(?:me\s+)?in\s+(\d+(?:\.\d+)?)\s*(second|sec|minute|min|hour|hr)s?\s*(?:to|that|about)?\s*(.*)",
        cleaned
    )
    if match:
        amount = float(match.group(1))
        unit = match.group(2)
        message = match.group(3).strip()

        multiplier = 1
        if "min" in unit:
            multiplier = 60
        elif "hour" in unit or "hr" in unit:
            multiplier = 3600

        seconds = amount * multiplier
        if not message:
            message = "your scheduled reminder is due"

        return {"seconds": seconds, "message": message, "amount": amount, "unit": unit}

    # Pattern 2: remind me to Y in X (seconds|minutes|hours)
    match2 = re.search(
        r"remind\s+(?:me\s+)?(?:to|that|about)?\s*(.*?)\s+in\s+(\d+(?:\.\d+)?)\s*(second|sec|minute|min|hour|hr)s?$",
        cleaned
    )
    if match2:
        message = match2.group(1).strip()
        amount = float(match2.group(2))
        unit = match2.group(3)

        multiplier = 1
        if "min" in unit:
            multiplier = 60
        elif "hour" in unit or "hr" in unit:
            multiplier = 3600

        seconds = amount * multiplier
        if not message:
            message = "your scheduled reminder is due"

        return {"seconds": seconds, "message": message, "amount": amount, "unit": unit}

    # Pattern 3: set a timer for X (seconds|minutes|hours)
    timer_match = re.search(
        r"(?:set\s+a\s+)?timer\s+(?:for\s+)?(\d+(?:\.\d+)?)\s*(second|sec|minute|min|hour|hr)s?",
        cleaned
    )
    if timer_match:
        amount = float(timer_match.group(1))
        unit = timer_match.group(2)
        multiplier = 1
        unit_str = "second"
        if "min" in unit:
            multiplier = 60
            unit_str = "minute"
        elif "hour" in unit or "hr" in unit:
            multiplier = 3600
            unit_str = "hour"

        seconds = amount * multiplier
        return {"seconds": seconds, "message": f"Your {int(amount) if amount.is_integer() else amount} {unit_str} timer has finished", "amount": amount, "unit": unit}

    return None
