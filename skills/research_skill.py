"""
Deep Research Skill for J.A.R.V.I.S.
Handles voice requests to autonomously conduct multi-source web research
and generate structured executive Markdown reports.
"""

import re
from system_layer.research_agent import conduct_deep_research

skill = {
    "name": "Research Skill",
    "priority": 21,
}

TRIGGER_KEYWORDS = [
    "deep research",
    "research report",
    "conduct research",
    "prepare research",
    "compile research",
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if cmd.startswith("research ") or "research on " in cmd or "research about " in cmd:
        return True
    if "prepare a report on" in cmd or "generate a report on" in cmd:
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # Extract topic
    topic = cmd
    prefixes = [
        "deep research on",
        "deep research about",
        "deep research",
        "prepare research report on",
        "prepare a report on",
        "generate a report on",
        "conduct research on",
        "research report on",
        "research report",
        "research on",
        "research about",
        "research",
    ]

    for p in prefixes:
        if topic.startswith(p):
            topic = topic[len(p):].strip()
            break

    if not topic:
        return "Sir, please state the topic you would like me to research."

    return conduct_deep_research(topic)
