"""
Autonomous Protocol Studio & Workstation Macro Engine for J.A.R.V.I.S.
Coordinates complex multi-application desktop workflows from declarative config/protocols.json:
- Work Protocol (IDE + Chrome snapping, Focus Guard, calibrated audio)
- Deep Focus Protocol (Subdued lighting & volume, 60m Do-Not-Disturb)
- Night Coding Protocol (Low 25% brightness/volume, VS Code, ambient timer)
- Meeting Protocol (Crystal-clear 60% audio, desktop preparation)
- Clean Desk Protocol (Maid file deduplication, PSAPI RAM purge)
- Stealth Protocol (Desktop minimization, microphone privacy mute)
"""

import os
import json
import time
import threading
from typing import Dict, Any, Optional, List

from system_layer.app_controller import open_app
from system_layer.autopilot_controller import snap_window, show_desktop
from background_tasks.focus_guard import start_focus_session, stop_focus_session
from voice_engine.sound_effects import play_fx
from wake_word import set_privacy_mute

PROTOCOLS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "protocols.json"
)

# Global runtime state
_current_protocol: Optional[str] = None
_protocol_timestamp: float = 0.0


def load_protocols_config() -> Dict[str, Any]:
    """Load protocols from config/protocols.json with safe defaults."""
    if os.path.exists(PROTOCOLS_FILE):
        try:
            with open(PROTOCOLS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[PROTOCOLS LOAD ERROR]: {e}")
    return {}


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


def execute_protocol(protocol_key: str) -> str:
    """
    Execute a declarative Stark protocol by key (e.g. 'work', 'deep_focus', 'night_coding', 'clean_desk').
    Applies volume, brightness, apps with snapping, focus sessions, and optimizations.
    """
    global _current_protocol, _protocol_timestamp

    protocols = load_protocols_config()
    clean_key = protocol_key.lower().strip().replace(" ", "_").replace("_protocol", "")

    # Match aliases
    if clean_key in ["work", "working"]:
        clean_key = "work"
    elif clean_key in ["focus", "deep_focus", "deep"]:
        clean_key = "deep_focus"
    elif clean_key in ["night", "night_coding", "coding"]:
        clean_key = "night_coding"
    elif clean_key in ["meeting", "conference"]:
        clean_key = "meeting"
    elif clean_key in ["clean", "clean_desk", "maid"]:
        clean_key = "clean_desk"
    elif clean_key in ["stealth", "privacy"]:
        clean_key = "stealth"

    if clean_key not in protocols:
        return f"Protocol '{protocol_key}' not found in protocol studio, Sir. Available protocols: {', '.join(protocols.keys())}."

    cfg = protocols[clean_key]
    proto_name = cfg.get("name", clean_key.replace("_", " ").title())

    _current_protocol = proto_name
    _protocol_timestamp = time.time()

    def _async_worker():
        # 1. Volume
        if "volume" in cfg:
            set_system_volume(int(cfg["volume"]))

        # 2. Brightness
        if "brightness" in cfg:
            set_system_brightness(int(cfg["brightness"]))

        # 3. Privacy Mute
        if cfg.get("privacy_mute"):
            set_privacy_mute(True)

        # 4. Hide Desktop
        if cfg.get("hide_desktop"):
            show_desktop()

        # 5. Apps & Window Snapping
        apps = cfg.get("apps", [])
        snaps = cfg.get("snap", {})
        for app in apps:
            open_app(app)
            time.sleep(1.0)
            if app in snaps:
                snap_window(snaps[app])

        # 6. Focus Guard Timer
        if cfg.get("focus_minutes"):
            start_focus_session(int(cfg["focus_minutes"]))

        # 7. RAM Cache Purge
        if cfg.get("ram_purge"):
            try:
                from system_layer.system_control import purge_ram
                purge_ram()
            except Exception:
                pass

        # 8. Maid Protocol Cleanup
        if cfg.get("maid_protocol"):
            try:
                from system_layer.maid_controller import run_maid_protocol
                run_maid_protocol(cfg["maid_protocol"])
            except Exception:
                pass

        # 9. Audio chime
        sound_fx = cfg.get("sound_fx", "complete")
        play_fx(sound_fx)

    threading.Thread(target=_async_worker, daemon=True, name=f"Protocol_{clean_key}").start()
    return f"{proto_name} initiated, Sir. {cfg.get('description', 'Workstation calibrated.')}"


def list_protocols() -> str:
    """Return speech-formatted list of all available protocols."""
    protocols = load_protocols_config()
    if not protocols:
        return "No protocols currently defined in the protocol studio, Sir."

    lines = []
    for k, v in protocols.items():
        name = v.get("name", k.title())
        desc = v.get("description", "")
        lines.append(f"{name}: {desc}")

    return "Available Stark Protocols:\n" + "\n".join(f"- {l}" for l in lines)


# Backward-compatible direct helpers
def activate_work_protocol(duration_minutes: int = 45) -> str:
    return execute_protocol("work")


def activate_deep_focus_protocol(duration_minutes: int = 60) -> str:
    return execute_protocol("deep_focus")


def activate_night_protocol() -> str:
    return execute_protocol("night_coding")


def activate_meeting_protocol() -> str:
    return execute_protocol("meeting")


def activate_clean_desk_protocol() -> str:
    return execute_protocol("clean_desk")


def activate_stealth_protocol() -> str:
    return execute_protocol("stealth")


def activate_gaming_protocol() -> str:
    """Gaming protocol disabled by user directive."""
    return "Gaming mode is inactive in this workstation profile, Sir. Would you like to activate Work Protocol or Deep Focus instead?"


def get_protocol_status() -> str:
    """Return status of currently active protocol."""
    if not _current_protocol:
        return "All systems are operating in standard mode, Sir. No special protocol is currently active."

    elapsed = int((time.time() - _protocol_timestamp) // 60)
    return f"{_current_protocol} is currently active, running for {elapsed} minutes."
