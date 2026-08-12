import threading

running_tasks = {}

def start_task(name, target_function, *args):

    if name in running_tasks:
        return f"{name} already running."

    thread = threading.Thread(
        target=target_function,
        args=args,
        daemon=True
    )

    running_tasks[name] = thread
    thread.start()

    return f"{name} started."


def stop_task(name):

    if name in running_tasks:
        del running_tasks[name]
        return f"{name} stopped."

    return "Task not found."


def list_tasks():

    return list(running_tasks.keys())