# intent_router.py

def route_intent(command, memory=None, context=None):
    command = command.lower()

    # ----- SYSTEM CONTROL -----
    system_keywords = [
        "shutdown", "restart", "sleep", "open", "close",
        "volume", "mute", "lock"
    ]

    # ----- CALCULATION -----
    math_keywords = [
        "calculate", "plus", "minus", "multiply",
        "divide", "+", "-", "*", "/"
    ]

    # ----- TIME / DATE -----
    time_keywords = [
        "time", "date", "day", "today"
    ]

    # ----- BROWSER / SEARCH -----
    browser_keywords = [
        "search", "google", "youtube"
    ]
    
    if "volume" in command:
        return "system"
    
    if "increase" in command or "decrease" in command:
        return "system"
    # Decide intent
    if any(word in command for word in system_keywords):
        return "system"

    elif any(word in command for word in math_keywords):
        return "math"

    elif any(word in command for word in time_keywords):
        return "time"

    elif any(word in command for word in browser_keywords):
        return "browser"

    else:
        return "ai"