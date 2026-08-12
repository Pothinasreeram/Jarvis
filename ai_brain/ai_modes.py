current_mode = "normal"

MODES = {

    "normal": {
        "reply": "Normal mode activated.",
        "personality": "helpful assistant"
    },

    "coding": {
        "reply": "Coding mode activated.",
        "personality": "expert programmer"
    },

    "study": {
        "reply": "Study mode activated.",
        "personality": "educational tutor"
    },

    "gaming": {
        "reply": "Gaming mode activated.",
        "personality": "gaming assistant"
    },

    "hacker": {
        "reply": "Hacker mode activated.",
        "personality": "cybersecurity expert"
    }
}


def activate_mode(mode_name):

    global current_mode

    mode_name = mode_name.lower()

    if mode_name in MODES:
        current_mode = mode_name
        return MODES[mode_name]["reply"]

    return "That mode does not exist."


def get_current_mode():
    return current_mode


def get_mode_personality():

    return MODES[current_mode]["personality"]