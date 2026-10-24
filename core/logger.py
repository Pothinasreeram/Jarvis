"""
Structured Logging Subsystem for J.A.R.V.I.S.
Provides unified, timestamped, subsystem-tagged logging with automatic file persistence
and UI notification subscription hooks.
"""

import os
import sys
import threading
from datetime import datetime
from typing import Callable, Optional, List

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOGS_DIR, "jarvis_system.log")

_log_lock = threading.Lock()
_listeners: List[Callable[[str, str, str], None]] = []


def _ensure_log_dir():
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
    except Exception:
        pass


def add_log_listener(callback: Callable[[str, str, str], None]):
    """Subscribe a listener callback (tag, level, message) for real-time HUD updates."""
    with _log_lock:
        if callback not in _listeners:
            _listeners.append(callback)


def remove_log_listener(callback: Callable[[str, str, str], None]):
    """Unsubscribe a listener callback."""
    with _log_lock:
        if callback in _listeners:
            _listeners.remove(callback)


def _format_entry(tag: str, level: str, message: str) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{now_str}] [{level.upper():5s}] [{tag}]: {message}"


def log(tag: str, message: str, level: str = "INFO"):
    """
    Log a message with subsystem tag and severity level.
    Persists to logs/jarvis_system.log and prints to standard console.
    """
    entry = _format_entry(tag, level, message)

    with _log_lock:
        print(entry)
        _ensure_log_dir()
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except Exception:
            pass

        for listener in _listeners:
            try:
                listener(tag, level, message)
            except Exception:
                pass


def info(tag: str, message: str):
    log(tag, message, level="INFO")


def warn(tag: str, message: str):
    log(tag, message, level="WARN")


def error(tag: str, message: str):
    log(tag, message, level="ERROR")


def success(tag: str, message: str):
    log(tag, message, level="OK")


def hud(message: str):
    log("HUD", message, level="INFO")
