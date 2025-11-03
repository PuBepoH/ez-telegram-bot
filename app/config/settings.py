# pylint: disable=too-many-instance-attributes, too-many-locals
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from app.config.logging import logger


def sanitize_proxy_env():
    """
    checking env vars and remove socks proxy if presented
    """
    proxy_vars = [
        "ALL_PROXY",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "all_proxy",
        "http_proxy",
        "https_proxy",
    ]
    for var in proxy_vars:
        val = os.getenv(var, "")
        if "socks://" in val.lower():
            logger.warning("Invalid proxy scheme detected in %s=%r", var, val)
            logger.warning('Setting %s=""', var)
            os.environ.pop(var, None)


# load and fix env
load_dotenv()
sanitize_proxy_env()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    openai_api_key: str
    openai_model: str

    admin_user_id: int
    allowed_roles: tuple[str, ...]

    postgres_dsn: str
    maintenance_db_name: str
    redis_url: str

    chat_max_history_messages: int
    chat_max_stored_messages: int
    chat_ttl_seconds: int

    telegram_msg_max_len: int

    @staticmethod
    def from_env() -> "Settings":
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        postgres_dsn = os.getenv(
            "POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/bot"
        )
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        admin_user_id_raw = os.getenv("ADMIN_USER_ID", "161638965")

        if not telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")

        if not openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in .env")

        chat_max_history_messages_raw = os.environ.get(
            "CHAT_MAX_HISTORY_MESSAGES", "10"
        )
        chat_max_stored_messages_raw = os.environ.get("CHAT_MAX_STORED_MESSAGES", "200")
        chat_ttl_seconds_raw = os.environ.get(
            "CHAT_TTL_SECONDS", str(30 * 24 * 60 * 60)  # 30 days in seconds as default
        )

        admin_user_id = int(admin_user_id_raw)
        chat_max_history_messages = int(chat_max_history_messages_raw)
        chat_max_stored_messages = int(chat_max_stored_messages_raw)
        chat_ttl_seconds = int(chat_ttl_seconds_raw)

        # constants
        allowed_roles = ("admin", "user")
        maintenance_db_name = "postgres"
        telegram_msg_max_len = 4000

        return Settings(
            admin_user_id=admin_user_id,
            postgres_dsn=postgres_dsn,
            telegram_bot_token=telegram_bot_token,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            redis_url=redis_url,
            chat_max_history_messages=chat_max_history_messages,
            chat_max_stored_messages=chat_max_stored_messages,
            chat_ttl_seconds=chat_ttl_seconds,
            allowed_roles=allowed_roles,
            maintenance_db_name=maintenance_db_name,
            telegram_msg_max_len=telegram_msg_max_len,
        )


settings = Settings.from_env()
