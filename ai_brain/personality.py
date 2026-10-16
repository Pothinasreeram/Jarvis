import random


# ======================================================
# JARVIS PERSONALITY CORE — V7.1.1
# ======================================================

def random_response(responses):
    return random.choice(responses)


# ------------------------------------------------------
# GENERAL ACKNOWLEDGEMENTS
# ------------------------------------------------------

def acknowledgement():
    return random_response([
        "Understood.",
        "Got it.",
        "Certainly.",
        "Right away.",
        "Consider it done.",
        "On it.",
    ])


# ------------------------------------------------------
# LISTENING RESPONSES
# ------------------------------------------------------

def listening():
    return random_response([
        "I'm listening.",
        "Go ahead.",
        "I'm ready.",
        "Listening.",
        "Yes?",
    ])


# ------------------------------------------------------
# SIMPLE SUCCESS RESPONSES
# ------------------------------------------------------

def success():
    return random_response([
        "Done.",
        "Done.",
        "Completed.",
        "It's done.",
        "All set.",
    ])


# ------------------------------------------------------
# INFORMATION RESPONSES
# ------------------------------------------------------

def information(text):
    prefixes = [
        "",
        "Certainly. ",
        "Of course. ",
        "Here's what I found. ",
    ]

    return random.choice(prefixes) + text


# ------------------------------------------------------
# PERSONALITY SETTINGS
# ------------------------------------------------------

PERSONALITY = {
    "use_sir": False,
    "formal": False,
    "concise": True,
}