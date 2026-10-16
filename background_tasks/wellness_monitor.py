"""
Desk Ergonomics & Health Coach ("Wellness Protocol") for J.A.R.V.I.S.
Monitors continuous screen time via Windows API, tracks hydration in SQLite,
and enforces healthy micro-breaks and posture reminders.
"""

import ctypes
import os
import sqlite3
import threading
import time
from datetime import datetime
from typing import Dict, Any

from voice_engine.sound_effects import play_fx

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jarvis_memory.db")

DAILY_WATER_TARGET = 8
WORK_BREAK_INTERVAL_SEC = 50 * 60      # 50 minutes continuous work trigger
BREAK_IDLE_THRESHOLD_SEC = 3 * 60      # 3 minutes idle constitutes a break
HYDRATION_REMIND_INTERVAL_SEC = 60 * 60 # 60 minutes between hydration nudges

# State variables
_running = False
_thread = None
_lock = threading.Lock()

_continuous_active_sec = 0.0
_breaks_taken_today = 0
_last_break_alert_ts = 0.0
_last_water_alert_ts = time.time()
_speak_cb = None
_gui_notif_cb = None


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_uint),
        ('dwTime', ctypes.c_uint),
    ]


def _get_idle_seconds() -> float:
    """Returns number of seconds since last user keyboard or mouse input."""
    try:
        lii = _LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(lii)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
            millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            return max(0.0, millis / 1000.0)
    except Exception:
        pass
    return 0.0


def _init_wellness_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wellness_hydration (
                    log_date TEXT PRIMARY KEY,
                    glasses INTEGER NOT NULL DEFAULT 0,
                    last_logged TEXT
                );
            """)
            conn.commit()
    except Exception as e:
        print(f"[WELLNESS DB INIT ERROR]: {e}")

_init_wellness_db()


def _get_today_date_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def log_water_intake(glasses: int = 1) -> str:
    """Logs water intake for today."""
    today = _get_today_date_str()
    now_str = datetime.now().strftime("%H:%M")
    global _last_water_alert_ts
    _last_water_alert_ts = time.time()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT glasses FROM wellness_hydration WHERE log_date = ?;", (today,))
            row = cursor.fetchone()
            if row:
                new_count = row[0] + glasses
                cursor.execute(
                    "UPDATE wellness_hydration SET glasses = ?, last_logged = ? WHERE log_date = ?;",
                    (new_count, now_str, today)
                )
            else:
                new_count = glasses
                cursor.execute(
                    "INSERT INTO wellness_hydration (log_date, glasses, last_logged) VALUES (?, ?, ?);",
                    (today, new_count, now_str)
                )
            conn.commit()

        play_fx("complete")
        
        if new_count >= DAILY_WATER_TARGET:
            return f"Logged. That makes {new_count} glasses of water today, Sir! You have reached your daily hydration target. Outstanding."
        else:
            remaining = DAILY_WATER_TARGET - new_count
            return f"Logged. Total is now {new_count} of {DAILY_WATER_TARGET} glasses today. {remaining} more to target, Sir."
    except Exception as e:
        return f"Failed to log hydration: {e}"


def get_hydration_count() -> int:
    """Returns number of glasses logged today."""
    today = _get_today_date_str()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT glasses FROM wellness_hydration WHERE log_date = ?;", (today,))
            row = cursor.fetchone()
            if row:
                return row[0]
    except Exception:
        pass
    return 0


def reset_hydration() -> str:
    """Resets today's hydration tally."""
    today = _get_today_date_str()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE wellness_hydration SET glasses = 0 WHERE log_date = ?;", (today,))
            conn.commit()
        return "Daily hydration count reset to zero, Sir."
    except Exception as e:
        return f"Failed to reset hydration: {e}"


def get_wellness_summary() -> Dict[str, Any]:
    """Generates structured telemetry for HUD status badges."""
    with _lock:
        mins = int(_continuous_active_sec // 60)
        hours = mins // 60
        rem_mins = mins % 60
        if hours > 0:
            time_str = f"{hours}h {rem_mins}m"
        else:
            time_str = f"{mins}m"
        
        glasses = get_hydration_count()
        breaks = _breaks_taken_today
        active = _running

    badge = f"{time_str} | {glasses}/{DAILY_WATER_TARGET} 💧" if active else "OFFLINE"
    return {
        "active": active,
        "continuous_work_str": time_str,
        "continuous_seconds": _continuous_active_sec,
        "glasses_today": glasses,
        "daily_target": DAILY_WATER_TARGET,
        "breaks_today": breaks,
        "badge_text": badge
    }


def get_ergonomic_advice() -> str:
    """Returns rotating ergonomic and posture recommendations."""
    import random
    tips = [
        "Rule 20-20-20: Every 20 minutes, focus your eyes on an object at least 20 feet away for 20 seconds to prevent retinal fatigue.",
        "Posture Directive: Align ears over shoulders, keep elbows at a 90-degree angle, and ensure screen height meets horizontal eye level.",
        "Shoulder Reset: Gently pull your shoulder blades together and hold for five seconds to release upper back tension.",
        "Spine Decompression: Stand up, place both palms on your lower back, and gently arch backward while breathing deeply."
    ]
    return random.choice(tips)


def _wellness_worker():
    global _continuous_active_sec, _breaks_taken_today, _last_break_alert_ts, _last_water_alert_ts
    
    interval = 5.0
    idle_accumulator = 0.0

    while _running:
        try:
            idle_sec = _get_idle_seconds()

            with _lock:
                # If user is idle >= 3 minutes, they took a break
                if idle_sec >= BREAK_IDLE_THRESHOLD_SEC:
                    if _continuous_active_sec > 600: # if worked at least 10 mins before taking break
                        _breaks_taken_today += 1
                    _continuous_active_sec = 0.0
                else:
                    # User is actively working
                    _continuous_active_sec += interval

                curr_work = _continuous_active_sec

            # Check 50-minute continuous work limit
            now = time.time()
            if curr_work >= WORK_BREAK_INTERVAL_SEC and (now - _last_break_alert_ts) > 600:
                _last_break_alert_ts = now
                with _lock:
                    _continuous_active_sec = 0.0 # reset after alerting
                    _breaks_taken_today += 1

                play_fx("alert")
                msg = "Sir, you have been working at your desk for 50 continuous minutes. Protocol suggests stepping away, stretching, and rolling your shoulders."
                if _gui_notif_cb:
                    try:
                        _gui_notif_cb("WELLNESS: 50min screen time threshold reached. Take a 3min break.")
                    except Exception:
                        pass
                if _speak_cb:
                    try:
                        _speak_cb(msg)
                    except Exception:
                        pass

            # Check hourly hydration reminder
            if (now - _last_water_alert_ts) >= HYDRATION_REMIND_INTERVAL_SEC:
                _last_water_alert_ts = now
                glasses = get_hydration_count()
                if glasses < DAILY_WATER_TARGET and curr_work > 300: # only if user is at desk
                    play_fx("ack")
                    h_msg = f"Hydration check, Sir. You have logged {glasses} of {DAILY_WATER_TARGET} glasses today. A sip of water is recommended."
                    if _gui_notif_cb:
                        try:
                            _gui_notif_cb(f"WELLNESS: Hydration reminder ({glasses}/{DAILY_WATER_TARGET} glasses).")
                        except Exception:
                            pass
                    if _speak_cb:
                        try:
                            _speak_cb(h_msg)
                        except Exception:
                            pass

        except Exception as e:
            print(f"[WELLNESS LOOP ERROR]: {e}")

        time.sleep(interval)


def start_wellness_monitor(speak_callback=None, gui_notif_callback=None):
    """Starts the background wellness and posture tracking service."""
    global _running, _thread, _speak_cb, _gui_notif_cb
    if _running:
        return "Wellness protocol is already active, Sir."

    _speak_cb = speak_callback
    _gui_notif_cb = gui_notif_callback
    _running = True
    _thread = threading.Thread(target=_wellness_worker, daemon=True, name="WellnessMonitor")
    _thread.start()
    return "Wellness protocol engaged, Sir. Monitoring desk ergonomics and hydration."


def stop_wellness_monitor():
    """Stops the wellness monitor."""
    global _running
    if not _running:
        return "Wellness protocol is already inactive, Sir."
    _running = False
    return "Wellness protocol disengaged, Sir."


def is_wellness_active() -> bool:
    return _running
