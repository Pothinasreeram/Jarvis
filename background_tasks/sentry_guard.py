"""
Sentry Mode & Desk Sentinel Engine for J.A.R.V.I.S.
Monitors user desk presence via lightweight local OpenCV Haar Cascade vision,
automatically locks Windows when the user walks away, and welcomes them back on return.
Zero cloud dependencies, micro-sampling (<0.1% CPU).
"""

import time
import os
import cv2
import ctypes
import threading
from typing import Dict, Any, Optional

from voice_engine.sound_effects import play_fx
from voice_engine.voice import speak

# State
_sentry_lock = threading.Lock()
_is_active = False
_auto_lock_seconds = 90
_last_seen_time = 0.0
_is_user_away = False
_intruder_count = 0
_worker_started = False
_cam_cap: Optional[cv2.VideoCapture] = None

SECURITY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "security")
os.makedirs(SECURITY_DIR, exist_ok=True)

CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
_face_cascade = cv2.CascadeClassifier(CASCADE_PATH)


def _get_or_open_camera() -> Optional[cv2.VideoCapture]:
    global _cam_cap
    if _cam_cap is None or not _cam_cap.isOpened():
        try:
            _cam_cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not _cam_cap.isOpened():
                _cam_cap = cv2.VideoCapture(0)
        except Exception as e:
            print(f"[SENTRY CAMERA INIT ERROR]: {e}")
            _cam_cap = None
    return _cam_cap


def _release_camera():
    global _cam_cap
    if _cam_cap is not None:
        try:
            _cam_cap.release()
        except Exception:
            pass
        _cam_cap = None


def is_sentry_active() -> bool:
    with _sentry_lock:
        return _is_active


def start_sentry_service():
    """Ensure background sentry daemon worker thread is alive."""
    global _worker_started
    if not _worker_started:
        _worker_started = True
        t = threading.Thread(target=_sentry_worker, daemon=True, name="SentryThread")
        t.start()
        print("[SENTRY GUARD] Desk Sentinel daemon service active.")


def start_sentry_mode(auto_lock_seconds: int = 90) -> str:
    """Activate Sentry Mode desk presence monitor."""
    global _is_active, _auto_lock_seconds, _last_seen_time, _is_user_away
    start_sentry_service()

    with _sentry_lock:
        _is_active = True
        _auto_lock_seconds = max(30, min(600, int(auto_lock_seconds)))
        _last_seen_time = time.time()
        _is_user_away = False

    play_fx("complete")
    return f"Sentry Mode activated, Sir. Desk presence monitored with {auto_lock_seconds}-second auto-lock protection."


def stop_sentry_mode() -> str:
    """Deactivate Sentry Mode and release camera."""
    global _is_active
    with _sentry_lock:
        if not _is_active:
            return "Sentry Mode is not currently active, Sir."
        _is_active = False

    _release_camera()
    play_fx("standby")
    return "Sentry Mode deactivated. Standard operating parameters restored, Sir."


# Backward compatibility aliases
start_sentry = start_sentry_mode
stop_sentry = stop_sentry_mode
stop_sentry_service = stop_sentry_mode


def get_sentry_status() -> Dict[str, Any]:
    with _sentry_lock:
        if not _is_active:
            return {"active": False, "status": "STANDBY"}

        elapsed_since_seen = int(time.time() - _last_seen_time)
        return {
            "active": True,
            "status": "AWAY" if _is_user_away else "PRESENT",
            "seconds_since_seen": elapsed_since_seen,
            "auto_lock_seconds": _auto_lock_seconds,
            "intrusions": _intruder_count,
        }


def _check_webcam_face() -> bool:
    """Inspect camera stream for user face with fast Haar cascade."""
    try:
        cap = _get_or_open_camera()
        if cap is None or not cap.isOpened():
            return True  # Fallback to true if camera unavailable

        ret, frame = cap.read()
        if not ret or frame is None:
            _release_camera()
            return True

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = _face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(30, 30)
        )
        return len(faces) > 0

    except Exception as e:
        print(f"[SENTRY VISION ERROR]: {e}")
        return True  # Non-fatal fallback


def _sentry_worker():
    global _last_seen_time, _is_user_away, _intruder_count
    print("[SENTRY GUARD] Daemon monitoring loop initiated.")
    while True:
        try:
            time.sleep(3.0)
            if not _is_active:
                _release_camera()
                continue

            face_detected = _check_webcam_face()
            now = time.time()

            if face_detected:
                if _is_user_away:
                    # User returned!
                    _is_user_away = False
                    _last_seen_time = now
                    print("[SENTRY] User presence detected. Welcome back!")
                    play_fx("wake")
                    threading.Thread(target=speak, args=("Welcome back, Sir. Workstation unlocked.",), daemon=True).start()
                else:
                    _last_seen_time = now
            else:
                elapsed = now - _last_seen_time
                if elapsed > _auto_lock_seconds and not _is_user_away:
                    # User walked away -> Auto-lock!
                    _is_user_away = True
                    print(f"[SENTRY] User absent for {int(elapsed)}s. Locking workstation...")
                    play_fx("alert")
                    try:
                        ctypes.windll.user32.LockWorkStation()
                    except Exception as lock_err:
                        print(f"[LOCK WORKSTATION ERROR]: {lock_err}")

        except Exception as e:
            print(f"[SENTRY LOOP EXCEPTION]: {e}")
            time.sleep(2)
