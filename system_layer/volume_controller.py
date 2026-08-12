from pycaw.pycaw import AudioUtilities

def handle_volume_commands(command):
    command = command.lower()

    device = AudioUtilities.GetSpeakers()
    volume = device.EndpointVolume

    current = volume.GetMasterVolumeLevelScalar()

    if "up" in command:
        current = min(current + 0.1, 1.0)
        volume.SetMasterVolumeLevelScalar(current, None)
        return "Volume increased."

    elif "down" in command:
        current = max(current - 0.1, 0.0)
        volume.SetMasterVolumeLevelScalar(current, None)
        return "Volume decreased."

    elif "mute" in command:
        volume.SetMute(1, None)
        return "Volume muted."

    elif "unmute" in command:
        volume.SetMute(0, None)
        return "Volume unmuted."

    elif "maximum" in command or "max" in command:
        volume.SetMasterVolumeLevelScalar(1.0, None)
        return "Volume set to maximum."

    elif "minimum" in command:
        volume.SetMasterVolumeLevelScalar(0.0, None)
        return "Volume set to minimum."

    return None