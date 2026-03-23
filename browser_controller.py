
import webbrowser

def handle_browser_commands(command: str):

    command = command.lower()

    # GOOGLE SEARCH
    if "search" in command or "google" in command:
        query = command.replace("search", "").replace("google", "").strip()

        if not query:
            return "What should I search for?"

        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)

        return f"Searching Google for {query}"

    # YOUTUBE SEARCH
    elif "youtube" in command:
        query = command.replace("youtube", "").replace("search", "").strip()

        if not query:
            webbrowser.open("https://youtube.com")
            return "Opening YouTube"

        url = f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(url)

        return f"Searching YouTube for {query}"

    return None