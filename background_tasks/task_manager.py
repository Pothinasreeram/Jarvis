import threading

# ============================================================
# JARVIS BACKGROUND TASK MANAGER — V7.3.2
# ============================================================

running_tasks = {}
task_stop_events = {}


def start_task(name, target_function, *args):
    """
    Start a background task safely.

    Each task receives its own stop event so it can eventually
    shut itself down cleanly.
    """

    if name in running_tasks:
        thread = running_tasks[name]

        if thread.is_alive():
            return f"{name} is already running."

        # Clean up stale task entry
        del running_tasks[name]
        task_stop_events.pop(name, None)

    stop_event = threading.Event()

    def task_wrapper():
        try:
            target_function(*args, stop_event=stop_event)
        except TypeError:
            # Backward compatibility with existing tasks
            # that don't yet accept stop_event.
            try:
                target_function(*args)
            except Exception as e:
                print(f"[BACKGROUND TASK ERROR] {name}:", e)

        except Exception as e:
            print(f"[BACKGROUND TASK ERROR] {name}:", e)

        finally:
            print(f"[BACKGROUND TASK] {name} finished.")

            running_tasks.pop(name, None)
            task_stop_events.pop(name, None)

    thread = threading.Thread(
        target=task_wrapper,
        name=f"Jarvis-{name}",
        daemon=True
    )

    running_tasks[name] = thread
    task_stop_events[name] = stop_event

    thread.start()

    return f"{name} started."


def stop_task(name):
    """
    Request a background task to stop.

    The task itself must periodically check its stop_event.
    """

    if name not in running_tasks:
        return "Task not found."

    stop_event = task_stop_events.get(name)

    if stop_event:
        stop_event.set()

    print(f"[BACKGROUND TASK] Stop requested: {name}")

    return f"Stop requested for {name}."


def list_tasks():
    """
    Return currently running background tasks.
    """

    active_tasks = []

    for name, thread in list(running_tasks.items()):

        if thread.is_alive():
            active_tasks.append(name)

        else:
            running_tasks.pop(name, None)
            task_stop_events.pop(name, None)

    return active_tasks