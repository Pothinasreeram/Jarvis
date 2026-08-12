import ollama
from ddgs import DDGS


def search_internet(query):

    results = []

    try:

        with DDGS() as ddgs:

            for r in ddgs.text(query, max_results=5):

                results.append(r["body"])

    except Exception as e:

        print("Search Error:", e)

    return " ".join(results)


def ask_ai(query, memory=None):

    try:

        internet_data = search_internet(query)

        prompt = f"""
        You are Jarvis, an advanced AI assistant.

        Answer the user's question clearly and naturally.

        User Question:
        {query}

        Internet Information:
        {internet_data}

        Give a short useful answer.
        """

        response = ollama.chat(

            model="llama3",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]

        )

        return response["message"]["content"]

    except Exception as e:

        print("OLLAMA ERROR:", e)

        return "I encountered an AI processing error."