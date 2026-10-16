import re
import ollama
from datetime import datetime

from memory_layer.memory import remember_conversation
from memory_layer.sqlite_memory import get_memory_context_for_prompt


# ==========================================================
# CURRENT DATE
# ==========================================================

current_date = datetime.now().strftime("%B %d, %Y")


# ==========================================================
# CONTEXT BUILDER
# ==========================================================

def _build_system_message(memory, prompt=""):
    if memory is None:
        memory = {}

    name = memory.get("name", "Sir")
    entities = memory.get("entities", {})
    current = entities.get("current", {})
    current_entity = current.get("name", "")

    conversation = memory.get("conversation", [])
    recent_conversation = conversation[-8:]

    conversation_context = ""
    for item in recent_conversation:
        user_message = item.get("user", "")
        assistant_message = item.get("assistant", "")
        entity = item.get("entity", "")
        conversation_context += f"User: {user_message}\nJARVIS: {assistant_message}\n"
        if entity:
            conversation_context += f"Topic: {entity}\n"
        conversation_context += "\n"

    entity_context = ""
    if current_entity:
        entity_data = entities.get(current_entity, {})
        facts = entity_data.get("facts", {})
        if facts:
            entity_context += f"Current entity: {current_entity}\n"
            for key, value in facts.items():
                entity_context += f"{key}: {value}\n"

    # Dynamic long-term semantic memory retrieval
    long_term_memory = ""
    try:
        long_term_memory = get_memory_context_for_prompt(prompt)
    except Exception as mem_err:
        print("[AI BRAIN MEMORY RETRIEVAL ERROR]:", mem_err)

    long_term_section = ""
    if long_term_memory:
        long_term_section = f"""
==================================================
LONG-TERM USER MEMORY & KNOWN FACTS
==================================================
{long_term_memory}
"""

    system_message = f"""
You are JARVIS, an advanced personal AI assistant.

Current date:
{current_date}

User name:
{name}

Current conversation entity:
{current_entity}

Known information about the current entity:
{entity_context}
{long_term_section}
Recent conversation:
{conversation_context}

==================================================
BEHAVIOR RULES
==================================================

1. Maintain conversation context.
2. Use previous conversation turns when answering the current question.
3. If the user says he, she, him, her, his, their, they, it, or its, use the current conversation subject when appropriate.
4. Do not invent facts.
5. If information is unknown, clearly say that you do not know.
6. Distinguish real people from fictional characters.
7. Answer naturally instead of repeating the user's question.
8. Keep simple answers short and direct.
9. Do not automatically address the user as "Sir" in every response.
10. Use the user's actual name only when it is confidently known from memory.
11. If the user's name is unknown, do not invent a name or title.
12. Avoid repetitive greetings, acknowledgements, and phrases.
13. Do not mention these system instructions.
14. Do not claim that information is current unless it is actually available to you.
15. When previous conversation provides the answer, use it instead of unnecessarily repeating a long explanation.
16. Think like an intelligent personal assistant.
17. Prefer natural, concise, TTS-friendly responses.
18. Do not unnecessarily explain simple answers.
==================================================
"""
    return system_message, current_entity


# ==========================================================
# ASK AI STREAM (FAST SENTENCE-BY-SENTENCE STREAMING)
# ==========================================================

def ask_ai_stream(prompt, memory=None):
    """
    Stream AI responses sentence-by-sentence for ultra-low latency speech playback.
    Yields complete sentences as soon as they are formed.
    """
    if memory is None:
        memory = {}

    system_message, current_entity = _build_system_message(memory, prompt=prompt)

    try:
        response = ollama.chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            options={
                "temperature": 0.1,
                "num_ctx": 4096,
                "num_predict": 180
            },
            stream=True
        )

        buffer = ""
        full_tokens = []
        sentence_end_pattern = re.compile(r'([.!?]+(?:\s+|\n+))')

        for chunk in response:
            content = chunk.get("message", {}).get("content", "")
            if not content:
                continue
            buffer += content
            full_tokens.append(content)

            parts = sentence_end_pattern.split(buffer)
            if len(parts) > 2:
                for i in range(0, len(parts) - 2, 2):
                    sentence = (parts[i] + parts[i+1]).strip()
                    if sentence:
                        yield sentence
                buffer = parts[-1]

        remaining = buffer.strip()
        if remaining:
            yield remaining

        complete_answer = "".join(full_tokens).strip()
        if not complete_answer:
            complete_answer = "I am ready, Sir."

        try:
            remember_conversation(
                memory,
                prompt,
                complete_answer,
                current_entity
            )
        except Exception as memory_error:
            print("[CONVERSATION MEMORY ERROR]:", memory_error)

    except Exception as e:
        print("[AI ERROR]:", e)
        yield "I encountered a processing issue, Sir."


# ==========================================================
# ASK AI (BLOCKING WRAPPER)
# ==========================================================

def ask_ai(prompt, memory=None):
    """Blocking version returning complete reply."""
    sentences = list(ask_ai_stream(prompt, memory))
    return " ".join(sentences).strip()