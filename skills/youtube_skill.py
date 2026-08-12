import webbrowser

skill = {
    "name": "youtube",
    "priority": 1
}

def can_handle(command):
    return "youtube" in command

def execute(command):
    print("youtube_skill EXECUTED")

    webbrowser.open("https://www.youtube.com")

    return "Opening YouTube"