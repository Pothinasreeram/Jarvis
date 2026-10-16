import queue
import threading

from voice_engine.voice import speak

# ============================================================
# JARVIS BACKGROUND NOTIFICATION MANAGER — V7.3.3
# ============================================================

notification_queue = queue.Queue()
notification_thread = None
notification_running = False


def _notification_worker():
    """
    Process background notifications one at a time.

    All background notifications pass through this worker,
    preventing multiple background tasks from calling TTS
    simultaneously.
    """

    global notification_running

    print("[NOTIFICATION MANAGER] Started")

    while notification_running:

        try:
            notification = notification_queue.get(
                timeout=0.5
            )

        except queue.Empty:
            continue

        try:
            if notification:
                print(
                    "[BACKGROUND NOTIFICATION]",
                    notification
                )

                speak(notification)

        except Exception as e:
            print(
                "[NOTIFICATION ERROR]",
                e
            )

        finally:
            notification_queue.task_done()

    print("[NOTIFICATION MANAGER] Stopped")


def start_notification_manager():
    """
    Start the notification worker if it isn't already running.
    """

    global notification_thread
    global notification_running

    if notification_thread is not None:
        if notification_thread.is_alive():
            return "Notification manager already running."

    notification_running = True

    notification_thread = threading.Thread(
        target=_notification_worker,
        name="Jarvis-Notification-Manager",
        daemon=True
    )

    notification_thread.start()

    return "Notification manager started."


def stop_notification_manager():
    """
    Stop the notification worker safely.
    """

    global notification_running

    if not notification_running:
        return "Notification manager is not running."

    notification_running = False

    print(
        "[NOTIFICATION MANAGER] Stop requested."
    )

    return "Notification manager stopping."


def send_notification(message):
    """
    Queue a background notification.

    Background tasks should call this instead of calling
    speak() directly.
    """

    if not message:
        return False

    notification_queue.put(str(message))

    print(
        "[NOTIFICATION QUEUED]",
        message
    )

    return True