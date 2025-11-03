import json
from typing import Dict, List

import redis
from chatgpt_role_prompts import CHATGPT_ROLE_PROMPTS

from app.config import settings

redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def _key(username: str, chatgpt_role: str, thread_id: int | str) -> str:
    return f"chat_history:{username}:{chatgpt_role}:{thread_id}"


def append_message(
    username: str,
    chatgpt_role: str,
    thread_id: int | str,
    speaker_role: str,
    content: str,
) -> None:
    """
    save one message of chat history in Redis
    """
    key = _key(username, chatgpt_role, thread_id)
    entry = json.dumps({"role": speaker_role, "content": content})

    # append in the end
    redis_client.rpush(key, entry)

    # trim to keep only maximum msg or less
    redis_client.ltrim(key, -settings.chat_max_stored_messages, -1)

    # update TTL
    redis_client.expire(key, settings.chat_ttl_seconds)


def get_recent_history(
    username: str, chatgpt_role: str, thread_id: int | str
) -> List[Dict[str, str]]:
    """
    Get last MAX_HISTORY_MESSAGES of chat history from Redis
    in OpenAI-ready format. Guaranteed that system msg will be returned first
    """
    key = _key(username, chatgpt_role, thread_id)
    raw_items = redis_client.lrange(key, -settings.chat_max_history_messages, -1)
    messages = [json.loads(item) for item in raw_items]

    # check for system msg
    has_system = any(msg["role"] == "system" for msg in messages)

    if not has_system:
        system_prompt = CHATGPT_ROLE_PROMPTS.get(
            chatgpt_role, CHATGPT_ROLE_PROMPTS["default"]
        )
        messages.insert(0, {"role": "system", "content": system_prompt})

    return messages


def reset_history(username: str, chatgpt_role: str, thread_id: int | str) -> None:
    redis_client.delete(_key(username, chatgpt_role, thread_id))
