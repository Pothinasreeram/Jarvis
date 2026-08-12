import webbrowser
from urllib.parse import quote_plus

WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "chatgpt": "https://chat.openai.com",
    "gmail": "https://mail.google.com",
    "wikipedia": "https://www.wikipedia.org",
    "reddit": "https://www.reddit.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com"
}


def handle_browser_commands(command):

    command = command.lower().strip()

    # ---------- OPEN WEBSITE ----------

    if command.startswith("open "):

        site = command.replace("open", "").strip()

        if site in WEBSITES:
            webbrowser.open(WEBSITES[site])
            return f"Opening {site.title()}"

    # ---------- GOOGLE SEARCH ----------

    if command.startswith("search "):

        query = command.replace("search", "").strip()

        if not query:
            return "What should I search for?"

        webbrowser.open(
            f"https://www.google.com/search?q={quote_plus(query)}"
        )

        return f"Searching Google for {query}"

    # ---------- SEARCH GOOGLE FOR ----------

    if command.startswith("google "):

        query = command.replace("google", "").strip()

        webbrowser.open(
            f"https://www.google.com/search?q={quote_plus(query)}"
        )

        return f"Searching Google for {query}"

    # ---------- SEARCH YOUTUBE ----------

    if "youtube" in command and "open" not in command:

        query = (
            command.replace("youtube", "")
                   .replace("search", "")
                   .strip()
        )

        if query:

            webbrowser.open(
                f"https://www.youtube.com/results?search_query={quote_plus(query)}"
            )

            return f"Searching YouTube for {query}"

        webbrowser.open(WEBSITES["youtube"])
        return "Opening YouTube"

    return None