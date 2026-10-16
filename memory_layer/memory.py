import json
import os

from memory_layer.sqlite_memory import (
    store_fact as sqlite_store_fact,
    recall_fact as sqlite_recall_fact,
    search_memory,
    get_memory_context_for_prompt,
    parse_memory_command,
    get_all_facts,
    delete_fact
)


MEMORY_FILE = "memory.json"


# ==========================================================
# LOAD MEMORY
# ==========================================================

def load_memory():

    if not os.path.exists(MEMORY_FILE):

        return {
            "entities": {},
            "conversation": []
        }

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if "entities" not in data:
                data["entities"] = {}

            if "conversation" not in data:
                data["conversation"] = []

            return data

    except Exception as e:

        print(
            "[MEMORY LOAD ERROR]:",
            e
        )

        return {
            "entities": {},
            "conversation": []
        }


# ==========================================================
# SAVE MEMORY
# ==========================================================

def save_memory(data):

    try:

        with open(
            MEMORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

    except Exception as e:

        print(
            "[MEMORY SAVE ERROR]:",
            e
        )


# ==========================================================
# BASIC MEMORY
# ==========================================================

def remember(key, value):
    try:
        sqlite_store_fact(key, value, category="user_fact")
    except Exception as e:
        print("[SQLITE MEMORY ERROR]:", e)

    memory = load_memory()
    memory[key] = value
    save_memory(memory)

    return (
        f"I will remember that your "
        f"{key} is {value}."
    )


def recall(key):
    try:
        sql_val = sqlite_recall_fact(key)
        if sql_val:
            return f"Your {key} is {sql_val}."
    except Exception:
        pass

    memory = load_memory()
    if key in memory:
        return (
            f"Your {key} is "
            f"{memory[key]}."
        )

    return (
        f"I don't remember your {key}."
    )


# ==========================================================
# ENTITY MEMORY
# ==========================================================

def remember_entity(
    memory,
    name,
    entity_type="unknown"
):

    if "entities" not in memory:

        memory["entities"] = {}

    name = name.lower().strip()

    if not name:
        return

    # ------------------------------------------------------
    # Don't overwrite existing entity unnecessarily
    # ------------------------------------------------------

    if name not in memory["entities"]:

        memory["entities"][name] = {
            "type": entity_type,
            "facts": {},
            "aliases": []
        }

    else:

        if entity_type != "unknown":

            memory["entities"][name][
                "type"
            ] = entity_type

        if "facts" not in memory[
            "entities"
        ][name]:

            memory["entities"][name][
                "facts"
            ] = {}

        if "aliases" not in memory[
            "entities"
        ][name]:

            memory["entities"][name][
                "aliases"
            ] = []

    # ------------------------------------------------------
    # Set current entity
    # ------------------------------------------------------

    memory["entities"]["current"] = {
        "name": name,
        "type": memory["entities"][name][
            "type"
        ]
    }


# ==========================================================
# CURRENT ENTITY
# ==========================================================

def get_current_entity(memory):

    entities = memory.get(
        "entities",
        {}
    )

    current = entities.get(
        "current"
    )

    if not current:

        return None

    return current.get(
        "name"
    )


# ==========================================================
# ENTITY ALIASES
# ==========================================================

def remember_entity_alias(
    memory,
    entity,
    alias
):

    if not entity or not alias:
        return

    entity = entity.lower().strip()
    alias = alias.lower().strip()

    if not entity or not alias:
        return

    if "entities" not in memory:
        memory["entities"] = {}

    if entity not in memory[
        "entities"
    ]:

        memory["entities"][entity] = {
            "type": "unknown",
            "facts": {},
            "aliases": []
        }

    entity_data = memory[
        "entities"
    ][entity]

    if "aliases" not in entity_data:

        entity_data["aliases"] = []

    if alias not in entity_data[
        "aliases"
    ]:

        entity_data["aliases"].append(
            alias
        )

        print(
            f"[ALIAS SAVED]: "
            f"{alias} → {entity}"
        )


# ==========================================================
# RESOLVE ENTITY
# ==========================================================

def resolve_entity(
    memory,
    name
):

    if not name:
        return None

    name = name.lower().strip()

    entities = memory.get(
        "entities",
        {}
    )

    # ------------------------------------------------------
    # Exact entity
    # ------------------------------------------------------

    if name in entities:

        return name

    # ------------------------------------------------------
    # Alias lookup
    # ------------------------------------------------------

    for entity_name, entity_data in entities.items():

        if entity_name == "current":
            continue

        aliases = entity_data.get(
            "aliases",
            []
        )

        if name in aliases:

            return entity_name

    return None


# ==========================================================
# ENTITY FACT MEMORY
# ==========================================================

def remember_entity_fact(
    memory,
    entity,
    fact_key,
    value
):

    if not entity:
        return

    entity = entity.lower().strip()

    # Resolve alias to canonical entity

    resolved_entity = resolve_entity(
        memory,
        entity
    )

    if resolved_entity:

        entity = resolved_entity

    if "entities" not in memory:

        memory["entities"] = {}

    if entity not in memory[
        "entities"
    ]:

        memory["entities"][entity] = {
            "type": "unknown",
            "facts": {},
            "aliases": []
        }

    if "facts" not in memory[
        "entities"
    ][entity]:

        memory["entities"][entity][
            "facts"
        ] = {}

    memory["entities"][entity][
        "facts"
    ][fact_key] = value

    # ------------------------------------------------------
    # Keep this entity active
    # ------------------------------------------------------

    memory["entities"]["current"] = {
        "name": entity,
        "type": memory["entities"][entity][
            "type"
        ]
    }

    print(
        f"[FACT SAVED] "
        f"{entity} → "
        f"{fact_key} = {value}"
    )


# ==========================================================
# RECALL ENTITY FACT
# ==========================================================

def recall_entity_fact(
    memory,
    entity,
    fact_key
):

    if not entity:
        return None

    entity = entity.lower().strip()

    # Resolve aliases

    resolved_entity = resolve_entity(
        memory,
        entity
    )

    if resolved_entity:

        entity = resolved_entity

    entities = memory.get(
        "entities",
        {}
    )

    entity_data = entities.get(
        entity
    )

    if not entity_data:
        return None

    facts = entity_data.get(
        "facts",
        {}
    )

    return facts.get(
        fact_key
    )

# ==========================================================
# REFERENCE MEMORY
# ==========================================================

def remember_reference(
    memory,
    reference_type,
    value
):
    """
    Remember a conversational reference.

    Stores:
        1. The latest reference
        2. A history of references grouped by type

    Examples:

        entity  -> elon musk
        company -> SpaceX
        company -> Tesla
    """

    if not value:
        return

    value = str(value).strip()

    if not value:
        return

    # ======================================================
    # CREATE REFERENCE MEMORY
    # ======================================================

    if "references" not in memory:

        memory["references"] = {}

    references = memory["references"]

    # ======================================================
    # SAVE AS LAST REFERENCE
    # ======================================================

    references["last"] = {
        "type": reference_type,
        "value": value
    }

    # ======================================================
    # SAVE REFERENCE HISTORY
    # ======================================================

    if reference_type not in references:

        references[reference_type] = []

    # Don't save duplicates

    existing = [
        str(item).lower()
        for item in references[reference_type]
    ]

    if value.lower() not in existing:

        references[reference_type].append(
            value
        )

    print(
        f"[REFERENCE SAVED]: "
        f"{reference_type} -> {value}"
    )


def get_last_reference(memory):
    """
    Return the most recent conversational reference.

    Returns:
        {
            "type": "...",
            "value": "..."
        }

    or None.
    """

    references = memory.get(
        "references",
        {}
    )

    return references.get(
        "last"
    )


def get_last_reference_value(
    memory,
    reference_type=None
):
    """
    Return the value of the most recent reference.

    If reference_type is provided,
    only return it when the types match.
    """

    reference = get_last_reference(
        memory
    )

    if not reference:
        return None

    if (
        reference_type
        and reference.get("type") != reference_type
    ):
        return None

    return reference.get(
        "value"
    )


def get_references(
    memory,
    reference_type
):
    """
    Return all remembered references
    of a specific type.
    """

    references = memory.get(
        "references",
        {}
    )

    values = references.get(
        reference_type,
        []
    )

    if not isinstance(values, list):
        return []

    return values


# ==========================================================
# CONVERSATION MEMORY
# ==========================================================

def remember_conversation(
    memory,
    user_message,
    assistant_message,
    entity=None,
    reference_type=None,
    reference_value=None
):
    """
    Save a conversation turn.

    Optionally remembers:

        entity
        reference_type
        reference_value
    """

    if "conversation" not in memory:

        memory["conversation"] = []

    entry = {
        "user": user_message,
        "assistant": assistant_message
    }

    if entity:

        entry["entity"] = entity

    if reference_type and reference_value:

        entry["reference"] = {
            "type": reference_type,
            "value": reference_value
        }

        remember_reference(
            memory,
            reference_type,
            reference_value
        )

    memory["conversation"].append(
        entry
    )

    # Keep only the most recent
    # 10 conversation turns.

    memory["conversation"] = (
        memory["conversation"][-10:]
    )

    # Persist conversation

    save_memory(
        memory
    )

    print(
        "[CONVERSATION SAVED]:",
        user_message
    )


# ==========================================================
# GET CONVERSATION HISTORY
# ==========================================================

def get_conversation_history(
    memory,
    limit=5
):

    history = memory.get(
        "conversation",
        []
    )

    return history[-limit:]


# ==========================================================
# CLEAR CONVERSATION
# ==========================================================

def clear_conversation(memory):

    memory["conversation"] = []

    save_memory(
        memory
    )