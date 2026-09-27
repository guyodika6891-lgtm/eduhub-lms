import os
from openai import OpenAI

_client = None


def _client_get():
    global _client
    if _client is None and os.environ.get("OPENAI_API_KEY"):
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are EduHub AI, a friendly teaching assistant.
Answer student questions clearly and concisely.
Use simple language. Give examples when helpful.
If the question is off-topic, gently redirect to the course content.
"""


def ask_ai(question, context="", history=None):
    client = _client_get()
    if client is None:
        return "⚠️ AI is not configured. Add OPENAI_API_KEY to your environment."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context:
        messages.append({"role": "system",
                         "content": f"Course context:\n{context[:4000]}"})
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": question})

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI unavailable right now: {e}"