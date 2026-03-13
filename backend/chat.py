import os

from groq import Groq

SYSTEM_PROMPT = """\
You are the LexCorp Legal Assistant — a professional, knowledgeable AI that \
answers questions about LexCorp Law Firm's internal policies, billing, ethics \
rules, and procedures.

RULES:
1. Base your answers ONLY on the document excerpts provided below.
2. Cite the section or page when you reference specific information.
3. If the excerpts do not contain enough information, say so honestly.
4. Be concise but thorough. Use bullet points where appropriate.
5. Maintain a professional, courteous tone at all times.

DOCUMENT EXCERPTS:
{context}
"""


def _build_context(chunks: list) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[{i}] ({c['citation']})\n{c['text']}")
    return "\n\n".join(parts)


def ask(query: str, chunks: list, history: list | None = None) -> str:
    """Send the query + RAG context to Groq and return the assistant answer."""
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    context = _build_context(chunks)
    system_msg = SYSTEM_PROMPT.format(context=context)

    messages = [{"role": "system", "content": system_msg}]

    # Append conversation history (if any)
    if history:
        for entry in history:
            messages.append({
                "role": entry.get("role", "user"),
                "content": entry.get("content", ""),
            })

    messages.append({"role": "user", "content": query})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    except Exception as exc:
        return f"I'm sorry, I encountered an error while processing your request: {exc}"