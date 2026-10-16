"""
Autonomous Deep Research & Report Agent for J.A.R.V.I.S.
Performs multi-query live internet research across sources via DuckDuckGo,
synthesizes comprehensive findings with local LLaMA 3.1:8b,
and compiles professional executive Markdown briefs on the user's Desktop.
"""

import os
import re
import time
from datetime import datetime
from typing import List, Dict, Optional
from ddgs import DDGS
import ollama

from voice_engine.sound_effects import play_fx

USER_DIR = os.environ.get("USERPROFILE", "")
DESKTOP_DIR = os.path.join(USER_DIR, "OneDrive", "Desktop") if os.path.exists(os.path.join(USER_DIR, "OneDrive", "Desktop")) else os.path.join(USER_DIR, "Desktop")
RESEARCH_DIR = os.path.join(DESKTOP_DIR, "Research")
os.makedirs(RESEARCH_DIR, exist_ok=True)


def _search_sources(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Search DuckDuckGo and return title, snippet, and url."""
    results = []
    try:
        ddgs = DDGS()
        raw = list(ddgs.text(query, max_results=max_results))
        for item in raw:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("body", ""),
                "url": item.get("href", "")
            })
    except Exception as e:
        print(f"[RESEARCH SEARCH ERROR]: {e}")
    return results


def conduct_deep_research(topic: str) -> str:
    """
    Executes deep research on topic, compiles Markdown report, and saves to Desktop/Research/.
    Returns a TTS-friendly executive spoken summary.
    """
    clean_topic = topic.strip()
    if not clean_topic:
        return "Sir, please specify the research topic you wish to investigate."

    print(f"[RESEARCH AGENT] Initiating deep research on: '{clean_topic}'...")

    # Multi-angle search queries
    queries = [
        clean_topic,
        f"{clean_topic} latest developments analysis",
        f"{clean_topic} overview technical breakdown"
    ]

    all_sources = []
    seen_urls = set()

    for q in queries:
        sources = _search_sources(q, max_results=3)
        for s in sources:
            url = s.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_sources.append(s)

    if not all_sources:
        return f"Sir, I was unable to retrieve live research data on {clean_topic} at this moment."

    # Format source context for LLM
    source_context = ""
    citations_list = []
    for i, s in enumerate(all_sources[:7], 1):
        source_context += f"Source [{i}]: {s['title']}\nSnippet: {s['snippet']}\nURL: {s['url']}\n\n"
        citations_list.append(f"- [{s['title']}]({s['url']})")

    # Prompt local LLaMA 3.1:8b to synthesize structured report
    system_prompt = (
        "You are J.A.R.V.I.S., Tony Stark's personal research scientist and intelligence analyst.\n"
        "Synthesize the provided research data into an executive, highly structured research brief.\n"
        "Format using clean GitHub Markdown:\n"
        "# Executive Research Brief: [Topic]\n"
        "**Date:** [Current Date] | **Prepared By:** J.A.R.V.I.S. Neural Core\n\n"
        "## 1. Executive Summary\n"
        "(3 to 4 sentences highlighting core findings)\n\n"
        "## 2. Key Breakthroughs & Developments\n"
        "(Detailed bullet points and explanations)\n\n"
        "## 3. Technical Implications & Analysis\n"
        "(Pros, challenges, and architectural assessment)\n\n"
        "## 4. Industry Impact & Outlook\n"
        "(What this means for the future)\n\n"
        "Do NOT include conversational chatter or intro filler."
    )

    user_prompt = f"Topic: {clean_topic}\n\nResearch Source Data:\n{source_context}"

    print("[RESEARCH AGENT] Synthesizing comprehensive report via LLaMA 3.1:8b...")
    try:
        response = ollama.chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            options={"temperature": 0.3}
        )
        report_content = response.get("message", {}).get("content", "").strip()

    except Exception as e:
        print(f"[RESEARCH LLM ERROR]: {e}")
        return f"Research data was collected, but report synthesis encountered an error, Sir."

    # Append References section
    citations_section = "\n\n## 5. Web Citations & References\n" + "\n".join(citations_list) + "\n"
    full_report = report_content + citations_section

    # Write file to Desktop/Research/
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    safe_topic = re.sub(r'[^\w\-_\. ]', '_', clean_topic).replace(' ', '_')[:35]
    filename = f"Report_{safe_topic}_{timestamp}.md"
    file_path = os.path.join(RESEARCH_DIR, filename)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_report)
        print(f"[RESEARCH AGENT] Saved report to: {file_path}")
        play_fx("complete")

        return (
            f"Deep research on {clean_topic} complete, Sir. I have synthesized {len(all_sources)} "
            f"sources into an executive brief and saved it to your Desktop Research folder."
        )

    except Exception as e:
        print(f"[RESEARCH SAVE ERROR]: {e}")
        return f"Research compiled successfully, but could not be written to disk: {e}"
