from pycaw.pycaw import AudioUtilities


skill = {
    "name": "Microphone Control Skill",
    "priority": 21,
}


MICROPHONE_NAME = "Microphone Array"


def get_microphone():
    try:
        devices = AudioUtilities.GetAllDevices()

        for device in devices:
            if MICROPHONE_NAME.lower() in device.FriendlyName.lower():
                return device

    except Exception as e:
        print("[MICROPHONE ERROR]", e)

    return None


def get_microphone_state():
    microphone = get_microphone()

    if microphone is None:
        return None

    try:
        return bool(microphone.EndpointVolume.GetMute())

    except Exception as e:
        print("[MICROPHONE ERROR]", e)
        return None


def mute_microphone():
    try:
        from wake_word import set_privacy_mute
        set_privacy_mute(True)
    except Exception:
        pass

    microphone = get_microphone()
    if microphone is not None:
        try:
            microphone.EndpointVolume.SetMute(1, None)
        except Exception:
            pass

    return "Microphone muted. Privacy Guard engaged, Sir. Tap the Arc Reactor or press Control Space to restore listening."


def unmute_microphone():
    try:
        from wake_word import set_privacy_mute
        set_privacy_mute(False)
    except Exception:
        pass

    microphone = get_microphone()
    if microphone is not None:
        try:
            microphone.EndpointVolume.SetMute(0, None)
        except Exception:
            pass

    return "Microphone unmuted. Neural listening operational, Sir."


def microphone_status():
    state = get_microphone_state()

    if state is None:
        return "I couldn't determine the microphone status."

    if state:
        return "The microphone is currently muted."

    return "The microphone is currently unmuted."


def can_handle(command):
    command = command.lower().strip()

    keywords = [
        "mute microphone",
        "mute my microphone",
        "mute the microphone",
        "mute mic",
        "privacy mode",
        "enable privacy mode",
        "go deaf",
        "turn off mic",
        "turn off microphone",
        "unmute microphone",
        "unmute my microphone",
        "unmute the microphone",
        "unmute mic",
        "disable privacy mode",
        "turn on mic",
        "turn on microphone",
        "microphone status",
        "mic status",
        "is my microphone muted",
        "is my mic muted",
        "check microphone",
        "check my microphone",
    ]

    return any(keyword in command for keyword in keywords)


def execute(command):
    command = command.lower().strip()

    # ---------------- UNMUTE ----------------

    if any(kw in command for kw in [
        "unmute microphone", "unmute my microphone", "unmute the microphone",
        "unmute mic", "disable privacy mode", "turn on mic", "turn on microphone"
    ]):
        return unmute_microphone()


    # ---------------- MUTE ----------------

    if any(kw in command for kw in [
        "mute microphone", "mute my microphone", "mute the microphone",
        "mute mic", "privacy mode", "enable privacy mode", "go deaf",
        "turn off mic", "turn off microphone"
    ]):
        return mute_microphone()


    # ---------------- STATUS ----------------

    if (
        "microphone status" in command
        or "mic status" in command
        or "is my microphone muted" in command
        or "is my mic muted" in command
        or "check microphone" in command
        or "check my microphone" in command
    ):
        return microphone_status()


    return "I couldn't determine the requested microphone operation."