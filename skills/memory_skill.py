"""
JARVIS Memory Skill
Handles user memory instructions:
- "Jarvis, remember that my favorite language is Python"
- "Jarvis, what do you remember about me?"
- "Jarvis, forget my old phone number"
"""

from memory_layer.sqlite_memory import (
    store_fact,
    delete_fact,
    get_all_facts,
    parse_memory_command,
    recall_fact
)

skill = {
    "name": "Memory",
    "priority": 15
}


def can_handle(command: str) -> bool:
    parsed = parse_memory_command(command)
    return parsed is not None


def execute(command: str) -> str:
    parsed = parse_memory_command(command)
    if not parsed:
        return "I could not understand what you wanted me to remember, Sir."

    action, key, val = parsed

    if action == "remember":
        store_fact(key, val, category="user_fact")
        return f"I have committed to memory that your {key} is {val}, Sir."

    elif action == "summary":
        facts = get_all_facts()
        if not facts:
            return "I don't have any saved facts about you in my memory database yet, Sir."

        summary_parts = []
        for f in facts[:8]:
            k = f["key"].replace("_", " ")
            v = f["value"]
            summary_parts.append(f"your {k} is {v}")

        spoken = "Here is what I currently have in my memory: " + ", ".join(summary_parts) + "."
        return spoken

    elif action == "forget":
        success = delete_fact(key)
        if success:
            return f"I have removed {key} from my long-term memory, Sir."
        else:
            return f"I could not find any memory for {key} to forget, Sir."

    return "Memory command processed, Sir."
