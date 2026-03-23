import subprocess
import webbrowser
import time

TASK_PLANS = {

    "coding mode": [
        lambda: subprocess.Popen("code"),
        lambda: webbrowser.open("https://github.com"),
        lambda: webbrowser.open("https://stackoverflow.com")
    ],

    "research mode": [
        lambda: webbrowser.open("https://google.com"),
        lambda: webbrowser.open("https://wikipedia.org"),
        lambda: webbrowser.open("https://chat.openai.com")
    ],

    "study mode": [
        lambda: webbrowser.open("https://youtube.com"),
        lambda: webbrowser.open("https://notion.so")
    ]

}


def execute_task_plan(command):

    command = command.lower()

    for task_name, actions in TASK_PLANS.items():

        if task_name in command:

            for action in actions:
                action()
                time.sleep(1)

            return f"{task_name.title()} activated."

    return None