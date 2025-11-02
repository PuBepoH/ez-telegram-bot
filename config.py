import logging
import os

import redis
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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

# read config values
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "161638965")
POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/bot"
)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CHAT_MAX_HISTORY_MESSAGES = int(os.getenv("CHAT_MAX_HISTORY_MESSAGES", "10"))
CHAT_MAX_STORED_MESSAGES = int(os.getenv("CHAT_MAX_STORED_MESSAGES", "200"))
CHAT_TTL_SECONDS = int(os.getenv("CHAT_TTL_SECONDS", str(30 * 24 * 60 * 60)))

# constants
ALLOWED_ROLES = ("admin", "user")
MAINTENANCE_DB_NAME = "postgres"

# init clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
