import os
import logging
from dotenv import load_dotenv

# --- load secrets ---
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def sanitize_proxy_env():
    """
    checking env vars and remove socks proxy if presented
    """
    proxy_vars = [
        "ALL_PROXY", "HTTP_PROXY", "HTTPS_PROXY",
        "all_proxy", "http_proxy", "https_proxy",     
    ]
    for var in proxy_vars:
        val = os.getenv(var, "")
        if "socks://" in val.lower():
            logger.warning(f"Invalid proxy scheme detected in {var} : {val}")
            logger.warning(f"Setting {var}=\"\"")
            os.environ.pop(var, None)

sanitize_proxy_env()


from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# OpenAI client initialization
client = OpenAI(api_key=OPENAI_API_KEY)


# ---------- function for communication with GPT ----------
def ask_gpt(user_message: str) -> str:
    """
    send user text to OpenAI and return response
    """
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "Ты — дружелюбный помощник. Отвечай кратко и по делу."},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
    )

    answer = response.choices[0].message.content
    return answer.strip()
    #return "some ChatGPT answer placeholder"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start handler
    """
    await update.message.reply_text(
        "Привет, я ezBot! Я могу отправлять твои запросы к ChatGPT и возвращать ответы. Погнали?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    forward default message to GPT and return response
    """

    user_text = update.message.text

    if not user_text or user_text.strip() == "":
        await update.message.reply_test("Мне нужен текст запроса. Не могу отправить пустой")
        return
    
    
    # call OpenAI model
    answer = ask_gpt(user_text)

    # send user response back
    # Telegram has msg length limit for ~4096 symbols
    MAX_LEN = 4000
    for i in range(0, len(answer), MAX_LEN):
        chunk = answer[i : i + MAX_LEN]
        await update.message.reply_text(chunk)


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start_command))

    # regular messages
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # launch long pollin
    app.run_polling()

if __name__ == "__main__":
    main()