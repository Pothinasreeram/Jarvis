"""
Focus Guard & Deep Work Enforcer for J.A.R.V.I.S.
Background AI Pomodoro monitor that tracks focus sessions, detects distracting
apps/browser windows, gives verbal interventions, and can close distractions on voice command.
"""

import time
import threading
from typing import Optional, Dict, Any

from voice_engine.sound_effects import play_fx
from voice_engine.voice import speak

# State
_focus_lock = threading.Lock()
_is_active = False
_duration_minutes = 25
_start_time = 0.0
_end_time = 0.0
_distractions_intercepted = 0
_last_warning_time = 0.0
_last_warned_app = ""
_pending_close_hwnd: Optional[int] = None
_pending_close_title: str = ""

# Monitored Distractions
DISTRACTION_PROCESSES = {
    "discord.exe": "Discord",
    "steam.exe": "Steam",
    "steamwebhelper.exe": "Steam",
    "epicgameslauncher.exe": "Epic Games",
    "telegram.exe": "Telegram",
    "riotclientux.exe": "Riot Games",
    "leagueclient.exe": "League of Legends",
    "valorant.exe": "Valorant",
    "genshinimpact.exe": "Genshin Impact",
    "battle.net.exe": "Battle.net",
}

DISTRACTION_TITLE_KEYWORDS = [
    "youtube",
    "reddit",
    "twitter",
    "x.com",
    "instagram",
    "facebook",
    "tiktok",
    "netflix",
    "twitch",
    "9gag",
    "shorts - youtube",
    "reels",
]

# Excluded titles (e.g. IDEs, research, or Jarvis itself)
SAFE_TITLE_KEYWORDS = [
    "visual studio",
    "code",
    "pycharm",
    "terminal",
    "powershell",
    "github",
    "stackoverflow",
    "arxiv",
    "j.a.r.v.i.s.",
    "chatgpt",
    "claude",
    "gemini",
]


def start_focus_session(minutes: int = 25) -> str:
    """Start an active focus / deep work session."""
    global _is_active, _duration_minutes, _start_time, _end_time, _distractions_intercepted
    global _last_warning_time, _last_warned_app, _pending_close_hwnd

    duration = max(1, min(180, int(minutes)))
    now = time.time()

    with _focus_lock:
        _is_active = True
        _duration_minutes = duration
        _start_time = now
        _end_time = now + (duration * 60)
        _distractions_intercepted = 0
        _last_warning_time = 0.0
        _last_warned_app = ""
        _pending_close_hwnd = None

    play_fx("complete")
    return f"Focus Protocol activated for {duration} minutes. Distraction guard is active."


def stop_focus_session() -> str:
    """End the current focus session early."""
    global _is_active
    with _focus_lock:
        if not _is_active:
            return "No active focus session is currently running."
        _is_active = False
        blocked = _distractions_intercepted

    play_fx("standby")
    return f"Focus session concluded. You intercepted {blocked} potential distractions."


def get_focus_status() -> Dict[str, Any]:
    """Get current session status dictionary."""
    with _focus_lock:
        if not _is_active:
            return {
                "active": False,
                "remaining_seconds": 0,
                "remaining_str": "00:00",
                "duration_minutes": _duration_minutes,
                "distractions_intercepted": _distractions_intercepted,
            }

        now = time.time()
        rem_sec = max(0, int(_end_time - now))
        mins = rem_sec // 60
        secs = rem_sec % 60
        return {
            "active": True,
            "remaining_seconds": rem_sec,
            "remaining_str": f"{mins:02d}:{secs:02d}",
            "duration_minutes": _duration_minutes,
            "distractions_intercepted": _distractions_intercepted,
        }


def close_pending_distraction() -> bool:
    """Close or minimize the recently flagged distracting window."""
    global _pending_close_hwnd, _pending_close_title
    hwnd = _pending_close_hwnd
    if not hwnd:
        return False

    try:
        import win32gui
        import win32con
        if win32gui.IsWindow(hwnd):
            # Send graceful WM_CLOSE
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            _pending_close_hwnd = None
            play_fx("complete")
            return True
    except Exception as e:
        print(f"[FOCUS GUARD CLOSE ERROR]: {e}")

    return False


def _check_foreground_distraction():
    """Detect if the active window is a monitored distraction."""
    global _distractions_intercepted, _last_warning_time, _last_warned_app
    global _pending_close_hwnd, _pending_close_title

    try:
        import win32gui
        import win32process
        import psutil

        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return

        title = win32gui.GetWindowText(hwnd).strip().lower()
        if not title:
            return

        # Check safe bypass
        if any(safe in title for safe in SAFE_TITLE_KEYWORDS):
            return

        app_name = None

        # 1. Process check
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid and psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                proc_name = proc.name().lower()
                if proc_name in DISTRACTION_PROCESSES:
                    app_name = DISTRACTION_PROCESSES[proc_name]
        except Exception:
            pass

        # 2. Window title keyword check (browsers, websites)
        if not app_name:
            for kw in DISTRACTION_TITLE_KEYWORDS:
                if kw in title:
                    app_name = kw.capitalize()
                    break

        if not app_name:
            return

        # Distraction matched!
        now = time.time()
        _distractions_intercepted += 1
        _pending_close_hwnd = hwnd
        _pending_close_title = app_name

        # Cooldown check: only alert once every 50 seconds per app
        if (now - _last_warning_time) > 50.0 or app_name != _last_warned_app:
            _last_warning_time = now
            _last_warned_app = app_name

            rem_sec = max(1, int(_end_time - now))
            mins_left = max(1, rem_sec // 60)

            play_fx("alert")
            prompt = (
                f"Sir, you are currently in a focus session with {mins_left} "
                f"minutes remaining. Shall I close {app_name} for you?"
            )
            # Speak in background without freezing loop
            threading.Thread(target=speak, args=(prompt,), daemon=True).start()

    except Exception:
        pass


def _focus_monitor_worker():
    """Main background loop polling active windows during focus sessions."""
    global _is_active
    while True:
        try:
            time.sleep(3.5)
            if not _is_active:
                continue

            now = time.time()
            if now >= _end_time:
                # Session complete!
                with _focus_lock:
                    _is_active = False
                    total_mins = _duration_minutes
                    intercepted = _distractions_intercepted

                play_fx("complete")
                congrats = (
                    f"Congratulations, Sir. Your {total_mins} minute focus session "
                    f"is complete. You had {intercepted} distractions intercepted. Excellent work."
                )
                threading.Thread(target=speak, args=(congrats,), daemon=True).start()
                continue

            _check_foreground_distraction()

        except Exception as e:
            time.sleep(2)


_worker_started = False

def start_focus_guard():
    """Start the background Focus Guard worker thread."""
    global _worker_started
    if not _worker_started:
        _worker_started = True
        t = threading.Thread(target=_focus_monitor_worker, daemon=True, name="FocusGuardThread")
        t.start()
        print("[FOCUS GUARD] Deep Work Enforcer service active.")
