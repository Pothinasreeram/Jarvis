"""
Stark Web Navigator Skill for J.A.R.V.I.S.
Handles voice requests for tech headlines, news briefs, and URL summarization.
"""

import re
from system_layer.web_agent import format_top_news_spoken, browse_and_summarize_url

skill = {
    "name": "Web Navigator Skill",
    "priority": 22,
}

TRIGGER_KEYWORDS = [
    "tech news",
    "top tech news",
    "hacker news",
    "tech headlines",
    "latest headlines",
    "browse url",
    "summarize url",
    "read url",
    "web headlines",
    "news briefing"
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if any(w in cmd for w in ["hacker news", "tech news", "headlines"]):
        return True
    if ("browse" in cmd or "summarize" in cmd) and any(w in cmd for w in ["http", ".com", ".org", ".io", ".net", ".edu"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # 1. URL summarization
    url_match = re.search(r'https?://[^\s]+|(?:www\.)?[a-zA-Z0-9-]+\.(?:com|org|io|net|edu|dev|ai)[^\s]*', cmd)
    if url_match:
        url = url_match.group(0)
        return browse_and_summarize_url(url)

    # 2. Tech headlines
    return format_top_news_spoken(limit=3)
