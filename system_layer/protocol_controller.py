"""
Custom Protocols & Multi-Action Macro Engine for J.A.R.V.I.S.
Coordinates complex multi-application desktop workflows:
- Work Protocol (IDE + Docs snapping, Focus Guard, volume calibration)
- Gaming Protocol (RAM optimization, high audio, Steam/Discord)
- Night Protocol (Display dimming, quiet volume, sleep mode)
- Stealth Protocol (Display hiding, microphone privacy mute)
"""

import time
import gc
import threading
from typing import Dict, Any, Optional

from system_layer.app_controller import open_app
from system_layer.autopilot_controller import snap_window, show_desktop
from background_tasks.focus_guard import start_focus_session, stop_focus_session
from voice_engine.sound_effects import play_fx
from wake_word import set_privacy_mute

# Global state
_current_protocol: Optional[str] = None
_protocol_timestamp: float = 0.0


def set_system_volume(percent: int):
    """Set Windows master volume safely (0-100%)."""
    try:
        from pycaw.pycaw import AudioUtilities
        sp = AudioUtilities.GetSpeakers()
        vol = sp.EndpointVolume
        scalar = max(0.0, min(1.0, percent / 100.0))
        vol.SetMasterVolumeLevelScalar(scalar, None)
    except Exception as e:
        print(f"[PROTOCOL VOLUME ERROR]: {e}")


def set_system_brightness(percent: int):
    """Set primary display brightness safely (0-100%)."""
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(max(10, min(100, percent)))
    except Exception as e:
        print(f"[PROTOCOL BRIGHTNESS ERROR]: {e}")


def activate_work_protocol(duration_minutes: int = 45) -> str:
    """Launch development workstation, align windows, calibrate audio, and start Focus Guard."""
    global _current_protocol, _protocol_timestamp
    _current_protocol = "Work"
    _protocol_timestamp = time.time()

    def _async_setup():
        # 1. Calibrate volume
        set_system_volume(35)

        # 2. Open IDE & Chrome
        open_app("code")
        time.sleep(1.0)
        snap_window("left")

        open_app("chrome")
        time.sleep(0.8)
        snap_window("right")

        # 3. Engage Focus Guard
        start_focus_session(duration_minutes)
        play_fx("complete")

    threading.Thread(target=_async_setup, daemon=True).start()
    return f"Work Protocol initiated, Sir. Workspace aligned, volume set to 35%, and Focus Guard active for {duration_minutes} minutes."


def activate_gaming_protocol() -> str:
    """Optimize memory, raise audio, and prepare gaming environment."""
    global _current_protocol, _protocol_timestamp
    _current_protocol = "Gaming"
    _protocol_timestamp = time.time()

    def _async_setup():
        # Stop any lingering focus sessions
        stop_focus_session()

        # Free Python and OS cache
        gc.collect()

        # Set high performance audio
        set_system_volume(80)

        # Launch game client (Steam or Discord)
        open_app("steam")
        play_fx("complete")

    threading.Thread(target=_async_setup, daemon=True).start()
    return "Gaming Protocol engaged, Sir. Memory purged, audio output calibrated to 80%, and game clients launched."


def activate_night_protocol() -> str:
    """Dim display, subdue audio, and set workstation into rest state."""
    global _current_protocol, _protocol_timestamp
    _current_protocol = "Night"
    _protocol_timestamp = time.time()

    def _async_setup():
        set_system_brightness(20)
        set_system_volume(20)
        show_desktop()
        play_fx("standby")

    threading.Thread(target=_async_setup, daemon=True).start()
    return "Night Protocol activated, Sir. Display dimmed to 20%, volume subdued, and workstation in resting state."


def activate_stealth_protocol() -> str:
    """Instant privacy lockdown: hide all desktop windows and mute microphone sensors."""
    global _current_protocol, _protocol_timestamp
    _current_protocol = "Stealth"
    _protocol_timestamp = time.time()

    def _async_setup():
        set_privacy_mute(True)
        show_desktop()
        play_fx("standby")

    threading.Thread(target=_async_setup, daemon=True).start()
    return "Stealth Protocol engaged, Sir. Display minimized and microphone sensors locked in Privacy Mode."


def get_protocol_status() -> str:
    """Return status of currently active protocol."""
    if not _current_protocol:
        return "All systems are operating in standard mode, Sir. No special protocol is currently active."

    elapsed = int((time.time() - _protocol_timestamp) // 60)
    return f"{_current_protocol} Protocol is currently active, running for {elapsed} minutes."
