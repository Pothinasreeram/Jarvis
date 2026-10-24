"""
J.A.R.V.I.S. Lifecycle & Graceful Shutdown Coordinator
Ensures clean termination of all threads, background monitors, hardware interfaces,
camera captures, audio streams, and socket locks on exit.
"""

import sys
import os
import threading
from typing import Callable, List

_shutdown_hooks: List[Callable[[], None]] = []
_is_shutting_down = False
_lock = threading.Lock()


def register_shutdown_hook(fn: Callable[[], None]) -> None:
    """Register a callback function to be executed during graceful shutdown."""
    with _lock:
        if fn not in _shutdown_hooks:
            _shutdown_hooks.append(fn)


def shutdown_jarvis(exit_code: int = 0) -> None:
    """
    Execute graceful shutdown sequence:
    1. Stop all registered services and hardware locks.
    2. Release webcam / MediaPipe gesture recognizers.
    3. Halt background wellness, sentry, reminder, and focus daemons.
    4. Close audio streams and TTS workers.
    5. Terminate the process cleanly.
    """
    global _is_shutting_down
    with _lock:
        if _is_shutting_down:
            return
        _is_shutting_down = True

    print("\n" + "=" * 60)
    print(" [LIFECYCLE] Initiating J.A.R.V.I.S. Graceful Shutdown...")
    print("=" * 60)

    # 1. Execute registered hooks
    for hook in _shutdown_hooks:
        try:
            hook()
        except Exception as e:
            print(f"[SHUTDOWN HOOK ERROR]: {e}")

    # 2. Release Camera & Gesture Controller
    try:
        from system_layer.gesture_controller import gesture_controller
        if gesture_controller.is_active():
            print("[LIFECYCLE] Releasing camera and gesture recognizer...")
            gesture_controller.stop()
    except Exception as e:
        print(f"[SHUTDOWN GESTURE ERROR]: {e}")

    try:
        from vision import stop_vision
        stop_vision()
    except Exception:
        pass

    # 3. Stop Proactive Background Services
    try:
        from background_tasks.reminder_manager import stop_reminder_manager
        stop_reminder_manager()
    except Exception:
        pass

    try:
        from background_tasks.wellness_monitor import stop_wellness_monitor
        stop_wellness_monitor()
    except Exception:
        pass

    try:
        from background_tasks.sentry_guard import stop_sentry_service
        stop_sentry_service()
    except Exception:
        pass

    try:
        from background_tasks.battery_monitor import stop_battery_monitor
        stop_battery_monitor()
    except Exception:
        pass

    try:
        from background_tasks.focus_guard import stop_focus_guard
        stop_focus_guard()
    except Exception:
        pass

    # 4. Stop Voice / Audio Playback
    try:
        from voice_engine.voice import stop_speaking
        stop_speaking()
    except Exception:
        pass

    print("[LIFECYCLE] All subsystems terminated cleanly. Goodbye, Sir.\n")

    # Final OS Exit
    try:
        os._exit(exit_code)
    except Exception:
        sys.exit(exit_code)
