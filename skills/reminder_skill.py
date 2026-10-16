"""
JARVIS Reminder & Timer Skill
Handles setting voice reminders and timers:
- "Jarvis, remind me in 5 minutes to submit the report"
- "Jarvis, set a timer for 10 minutes"
- "Jarvis, what reminders do I have?"
"""

from background_tasks.reminder_manager import (
    add_reminder,
    get_active_reminders,
    cancel_reminder,
    parse_reminder_phrase
)

skill = {
    "name": "Reminder",
    "priority": 20
}


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if parse_reminder_phrase(cmd) is not None:
        return True
    if any(p in cmd for p in ["list reminders", "active reminders", "show reminders", "cancel reminder"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    if any(p in cmd for p in ["list reminders", "active reminders", "show reminders"]):
        reminders = get_active_reminders()
        if not reminders:
            return "You have no active timers or reminders, Sir."
        parts = []
        for r in reminders:
            secs = r["seconds_left"]
            if secs >= 60:
                mins = round(secs / 60, 1)
                parts.append(f"'{r['message']}' in {mins} minutes")
            else:
                parts.append(f"'{r['message']}' in {secs} seconds")
        return "Active reminders: " + ", ".join(parts) + "."

    if "cancel reminder" in cmd:
        reminders = get_active_reminders()
        if not reminders:
            return "There are no reminders to cancel, Sir."
        last_id = reminders[-1]["id"]
        cancel_reminder(last_id)
        return "I have cancelled your last reminder, Sir."

    parsed = parse_reminder_phrase(cmd)
    if parsed:
        add_reminder(parsed["seconds"], parsed["message"])
        amount_str = f"{int(parsed['amount']) if parsed['amount'].is_integer() else parsed['amount']}"
        unit_str = parsed["unit"]
        if not unit_str.endswith("s"):
            unit_str += "s"
        return f"Understood, Sir. I will remind you in {amount_str} {unit_str}."

    return "I couldn't parse the requested reminder time, Sir."
