"""
Stark Web Agent & Autonomous Web Navigator for J.A.R.V.I.S.
Fetches real-time tech news, extracts article content, and synthesizes web intelligence.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

from voice_engine.sound_effects import play_fx
from ai_brain.ai_brain import ask_ai


def get_top_tech_news(limit: int = 3) -> List[Dict[str, Any]]:
    """Fetch top tech headlines from Hacker News API with fast fallback."""
    stories = []
    try:
        resp = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=4)
        if resp.status_code == 200:
            ids = resp.json()[:limit * 2]
            for sid in ids:
                try:
                    item_resp = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=3)
                    if item_resp.status_code == 200:
                        data = item_resp.json()
                        title = data.get("title", "")
                        url = data.get("url", f"https://news.ycombinator.com/item?id={sid}")
                        score = data.get("score", 0)
                        if title and not any(s["title"] == title for s in stories):
                            stories.append({
                                "title": title,
                                "url": url,
                                "score": score,
                                "source": "Hacker News"
                            })
                        if len(stories) >= limit:
                            break
                except Exception:
                    continue
    except Exception as e:
        print(f"[HN FETCH ERROR]: {e}")

    # Fallback to DuckDuckGo search if HN failed
    if not stories:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.news("AI technology breakthroughs", max_results=limit))
                for r in results:
                    stories.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "score": 100,
                        "source": r.get("source", "Web News")
                    })
        except Exception:
            pass

    return stories


def format_top_news_spoken(limit: int = 3) -> str:
    """Format top tech news into spoken audio briefing."""
    stories = get_top_tech_news(limit=limit)
    if not stories:
        return "I was unable to retrieve live tech headlines at this moment, Sir."

    play_fx("complete")
    spoken_parts = []
    for i, s in enumerate(stories, 1):
        clean_title = s['title'].replace("&quot;", '"').replace("&amp;", "&")
        spoken_parts.append(f"Headline {i}: {clean_title}")

    return f"Here are the top tech headlines, Sir. " + ". ".join(spoken_parts) + "."


def browse_and_summarize_url(url: str) -> str:
    """Download web page text and synthesize with LLaMA 3.1:8b into 3 executive takeaways."""
    clean_url = url.strip()
    if not clean_url.startswith("http"):
        clean_url = "https://" + clean_url

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(clean_url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return f"Failed to retrieve page: HTTP error {resp.status_code}, Sir."

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 40]
        text_corpus = " ".join(paragraphs[:15])

        if not text_corpus:
            return "I accessed the URL, Sir, but found no readable article body content."

        prompt = (
            f"You are J.A.R.V.I.S., Tony Stark's AI assistant. "
            f"Read the following web page content and synthesize 3 concise, high-impact bullet points "
            f"summarizing the key findings, followed by a one-sentence executive verdict. "
            f"Content: {text_corpus[:3500]}"
        )

        play_fx("complete")
        summary = ask_ai(prompt)
        return summary

    except Exception as e:
        return f"Encountered an error while browsing the requested URL: {e}"


def answer_with_web_research(query: str):
    """Search DuckDuckGo and synthesize concise spoken answer with local LLaMA 3.1."""
    sources = []
    snippets = []
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for r in results:
                title = r.get("title", "")
                body = r.get("body", "")
                href = r.get("href", "")
                if href:
                    sources.append(href)
                snippets.append(f"{title}: {body}")
    except Exception as e:
        print(f"[DDG SEARCH ERROR]: {e}")

    if not snippets:
        return f"I could not retrieve live web search results for '{query}', Sir.", []

    prompt = (
        f"You are J.A.R.V.I.S., Tony Stark's personal assistant. "
        f"Based on the following live web search results, answer the user's query concisely in 2 to 3 sentences in character: "
        f"User Query: {query}\n\nSearch Results:\n" + "\n".join(snippets)
    )

    play_fx("complete")
    answer = ask_ai(prompt)
    return answer, sources
