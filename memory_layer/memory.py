import json
import os

MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}

    with open(MEMORY_FILE, "r") as file:
        return json.load(file)


def save_memory(data):
    with open(MEMORY_FILE, "w") as file:
        json.dump(data, file, indent=4)

def remember(key, value):
    memory = load_memory()
    memory[key] = value
    save_memory(memory)
    return f"I will remember that your {key} is {value}."


def recall(key):
    memory = load_memory()

    if key in memory:
        return f"Your {key} is {memory[key]}."
    else:
        return f"I don't remember your {key}."