from openai import OpenAI

from app.config import settings

openai_client = OpenAI(api_key=settings.openai_api_key)


def ask_gpt(user_text_and_context: list[dict[str, str]]) -> str:
    """
    Send user text to OpenAI and return response
    """
    response = openai_client.chat.completions.create(
        model=settings.openai_model,
        messages=user_text_and_context,
        temperature=0.7,
    )

    raw_answer = response.choices[0].message.content
    if raw_answer is None:
        return ""
    return str(raw_answer).strip()
