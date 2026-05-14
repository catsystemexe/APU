import os
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def call_model(system_instructions: str, user_message: str) -> str:
    """
    Role-based input (system + user) pro lepší determinismus a parity s Custom GPT.
    """
    try:
        resp = await client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_message},
            ],
        )

        text = getattr(resp, "output_text", None)
        if text:
            return text

        parts = []
        for item in (resp.output or []):
            for c in getattr(item, "content", []) or []:
                t = getattr(c, "text", None)
                if t:
                    parts.append(t)

        return "\n".join(parts).strip() or "[EMPTY_RESPONSE]"
    except Exception as e:
        return f"[MODEL_ERROR] {type(e).__name__}: {e}"