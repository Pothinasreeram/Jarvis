"""
JARVIS Memory Skill
Handles user memory instructions:
- "Jarvis, remember that my favorite language is Python"
- "Jarvis, what do you remember about me?"
- "Jarvis, search memory for scraper"
- "Jarvis, do you remember my dog's name?"
- "Jarvis, forget my old phone number"
"""

from memory_layer.sqlite_memory import (
    store_fact,
    delete_fact,
    get_all_facts,
    parse_memory_command,
    recall_fact,
    search_all_memory,
)

skill = {
    "name": "Memory",
    "priority": 15,
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

    elif action == "search":
        search_res = search_all_memory(key)
        facts = search_res.get("facts", [])
        convos = search_res.get("conversations", [])

        if not facts and not convos:
            return f"I scanned your long-term memory and conversation archives, Sir, but found no matching records for '{key}'."

        responses = []
        if facts:
            top_f = facts[0]
            k = top_f["key"].replace("_", " ")
            v = top_f["value"]
            responses.append(f"Regarding {k}, your saved record is {v}.")

        if convos:
            top_c = convos[0]
            q = top_c["user_prompt"]
            a = top_c["assistant_response"]
            a_snippet = (a[:140] + "...") if len(a) > 140 else a
            responses.append(f"In a previous session regarding '{q}', I noted: {a_snippet}")

        return " ".join(responses)

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
