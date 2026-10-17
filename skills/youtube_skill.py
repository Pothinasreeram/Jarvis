"""
YouTube Navigation & Video Search Skill for J.A.R.V.I.S.
Handles voice requests to open YouTube or search for specific videos/music.
"""

import re
import webbrowser
from urllib.parse import quote_plus
from voice_engine.sound_effects import play_fx

skill = {
    "name": "YouTube Skill",
    "priority": 25
}


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if "spotify" in cmd:
        return False
    return "youtube" in cmd


def execute(command: str) -> str:
    cmd = command.lower().strip()
    play_fx("complete")

    # Patterns for extracting video queries
    patterns = [
        r'(?:search\s+youtube\s+for|search\s+on\s+youtube\s+for)\s+(.+)',
        r'(?:search\s+for|look\s+up)\s+(.+?)\s+on\s+youtube',
        r'(?:play|find)\s+(.+?)\s+on\s+youtube',
        r'youtube\s+(?:search|find|play)\s+(.+)',
        r'youtube\s+(.+)'
    ]

    query = None
    for pattern in patterns:
        match = re.search(pattern, cmd)
        if match:
            extracted = match.group(1).strip()
            # If extracted is just 'com' or empty, ignore
            if extracted and extracted not in ["com", ".com", "website", "app"]:
                query = extracted
                break

    # If a specific search query was extracted
    if query:
        encoded = quote_plus(query)
        webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
        return f"Searching YouTube for '{query}', Sir."

    # Default fallback: open YouTube homepage
    webbrowser.open("https://www.youtube.com")
    return "Opening YouTube, Sir."