import ollama

def ask_ai(prompt, memory):
    try:
        name = memory.get("name", "User")

        system_message = f"""
You are Jarvis, an advanced AI assistant inspired by Iron Man.

Rules:
- Always respond clearly.
- Never respond with an empty message.
- Keep answers concise but informative.
- Address the user as {name}.
"""

        response = ollama.chat(
            model="llama3:8b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            options={
                "temperature": 0.3,   # stable factual answers
                "num_ctx": 2048,      # reduces RAM pressure
                "num_predict": 200    # limits response length
            }
        )

        content = response["message"]["content"]

        if not content or content.strip() == "":
            return "I'm here, how can I assist you?"

        return content.strip()

    except Exception as e:
        print("AI Error:", e)
        return "I encountered a processing issue."