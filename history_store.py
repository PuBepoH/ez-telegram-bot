import json
from typing import List, Dict
from config import (
    redis_client,
    CHAT_MAX_HISTORY_MESSAGES,
    CHAT_MAX_STORED_MESSAGES,
    CHAT_TTL_SECONDS,
    )
from chatgpt_role_prompts import CHATGPT_ROLE_PROMPTS


def _key(username: str, chatgpt_role: str, thread_id: int | str) -> str:
    return f"chat_history:{username}:{chatgpt_role}:{thread_id}"

def append_message(username: str, chatgpt_role: str, thread_id: int | str, speaker_role: str, content: str) -> None:
    """
    save one message of chat history in Redis
    """
    key = _key(username, chatgpt_role, thread_id)
    entry = json.dumps({"role": speaker_role, "content": content})

    # append in the end
    redis_client.rpush(key, entry)

    # trim to keep only maximum msg or less
    redis_client.ltrim(key, -CHAT_MAX_STORED_MESSAGES, -1)

    # update TTL
    redis_client.expire(key, CHAT_TTL_SECONDS)

def get_recent_history(username: str, chatgpt_role: str, thread_id: int | str) -> List[Dict[str, str]]:
    """
    Get last MAX_HISTORY_MESSAGES of chat history from Redis
    in OpenAI-ready format. Guaranteed that system msg will be returned first
    """
    key = _key(username, chatgpt_role, thread_id)
    raw_items = redis_client.lrange(key, -CHAT_MAX_HISTORY_MESSAGES, -1)
    messages = [json.loads(item) for item in raw_items]

    # check for system msg
    has_system = any(msg["role"] == "system" for msg in messages)

    if not has_system:
        system_prompt = CHATGPT_ROLE_PROMPTS.get(chatgpt_role, CHATGPT_ROLE_PROMPTS["default"])
        messages.insert(0, {"role": "system", "content": system_prompt})

    return messages

def reset_history(username: str, chatgpt_role: str, thread_id: int | str) -> None:
    redis_client.delete(_key(username, chatgpt_role, thread_id))