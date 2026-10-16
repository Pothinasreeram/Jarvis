"""
JARVIS Autonomous Web Search & Live News Skill
Fetches live information from the internet and synthesizes spoken answers
using local LLaMA 3.1:8b.
"""

from system_layer.web_agent import answer_with_web_research

skill = {
    "name": "Live Web Search",
    "priority": 22
}

PREFIXES = [
    "search the web for ",
    "search web for ",
    "search online for ",
    "search for ",
    "look up ",
    "what is the latest news on ",
    "what is the latest news about ",
    "what is the latest on ",
    "latest news on ",
    "latest news about ",
    "news on ",
    "news about ",
    "what happened today regarding ",
    "what happened today with ",
    "what is the current price of ",
    "what is the score of ",
    "who won the ",
    "who won "
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()

    # Don't capture explicit browser requests
    if any(b in cmd for b in ["open browser", "open chrome", "in browser", "open website"]):
        return False

    # Check prefixes
    if any(cmd.startswith(p) for p in PREFIXES):
        return True

    # General news queries
    if ("latest news" in cmd or "breaking news" in cmd) and len(cmd.split()) >= 3:
        return True

    # If starts with 'search ' and not youtube
    if cmd.startswith("search ") and "youtube" not in cmd and len(cmd.split()) >= 2:
        return True

    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # Clean query text
    query = cmd
    for p in PREFIXES:
        if query.startswith(p):
            query = query[len(p):].strip()
            break

    if not query:
        query = cmd

    print(f"[LIVE WEB SEARCH] Querying internet for: '{query}'")

    try:
        answer, sources = answer_with_web_research(query)

        # Log sources in GUI notifications if available
        if sources:
            source_summary = ", ".join(sources[:2])
            print(f"[LIVE WEB SOURCES]: {source_summary}")

        return answer

    except Exception as e:
        print(f"[LIVE WEB SEARCH ERROR]: {e}")
        return "I encountered an issue connecting to the live network, Sir."
