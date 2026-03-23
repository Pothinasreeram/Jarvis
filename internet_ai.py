import requests
from ddgs import DDGS
import ollama
import webbrowser

def search_internet(query):

    url = f"https://duckduckgo.com/?q={query}"

    webbrowser.open(url)

    return "Sir, I have opened the latest news for you."
def search_internet(query):
    results = []

    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=5):
            results.append(r["body"])

    return " ".join(results)


def ask_ai(query):
    try:
        internet_data = search_internet(query)

        prompt = f"""
        Answer the question using the information below.

        Question: {query}

        Information:
        {internet_data}

        Give a short clear answer.
        """

        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )

        return response["message"]["content"]

    except:
        return None