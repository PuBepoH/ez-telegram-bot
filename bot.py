from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import history_store
from config import ALLOWED_ROLES, OPENAI_MODEL, TELEGRAM_BOT_TOKEN, openai_client
from db_init import init_db
from user_repo import TelegramUserData, UserRepo

user_repo = UserRepo()
telegram_user = TelegramUserData()
TELEGRAM_MSG_MAX_LEN = 4000  # Telegram has msg length limit for ~4096 symbols


def user_role_allowed(role: str) -> bool:
    return role in ALLOWED_ROLES


# ---------- function for communication with GPT ----------
def ask_gpt(user_text_and_context: list[dict[str, str]]) -> str:
    """
    send user text to OpenAI and return response
    """
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=user_text_and_context,
        temperature=0.7,
    )

    raw_answer = response.choices[0].message.content
    if raw_answer is None:
        return ""
    return str(raw_answer).strip()


async def start_command(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    /start handler
    """
    await update.message.reply_text(
        """
        Hello, I'm ezBot! 
        
        I can send requests to ChatGPT and return responses.
        """
    )


async def reset_command(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    /reset handler
    """
    telegram_user.tg_id = update.effective_user.id
    telegram_user.username = (
        update.effective_user.username or f"user_{telegram_user.tg_id}"
    )
    telegram_user.first_name = update.effective_user.first_name
    telegram_user.last_name = update.effective_user.last_name

    thread_id = 0

    role = user_repo.upsert_and_get_role(
        telegram_user,
        default_role="user",
    )

    if not user_role_allowed(role):
        await update.message.reply_text("⛔ You have no access to this bot.")
        return

    history_store.reset_history(
        username=telegram_user.username,
        chatgpt_role="default",
        thread_id=0,
    )

    await update.message.reply_text(
        """
        Your chat history for:

        User = %s,
        ChatGPT role = %s,
        Thread_id = %s
        
        Has been deleted.
        """,
        telegram_user.username,
        "default",
        thread_id,
    )


async def handle_message(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    forward default message to GPT and return response
    """
    telegram_user.tg_id = update.effective_user.id
    telegram_user.username = (
        update.effective_user.username or f"user_{telegram_user.tg_id}"
    )
    telegram_user.first_name = update.effective_user.first_name
    telegram_user.last_name = update.effective_user.last_name
    user_text = update.message.text

    thread_id = 0

    role = user_repo.upsert_and_get_role(
        telegram_user,
        default_role="user",
    )

    if not user_role_allowed(role):
        await update.message.reply_text("⛔ You have no access to this bot.")
        return

    if not user_text or user_text.strip() == "":
        await update.message.reply_text(
            "Мне нужен текст запроса. Не могу отправить пустой"
        )
        return

    # add user input to chat history
    history_store.append_message(
        telegram_user.username,
        "default",  # chatgpt_role
        thread_id,
        "user",  # speaker_role
        user_text,
    )

    # get chat history + user input
    user_text_and_context = history_store.get_recent_history(
        telegram_user.username, chatgpt_role="default", thread_id=0
    )

    # call OpenAI model
    answer = ask_gpt(user_text_and_context)

    # add OpenAI answer to chat history
    history_store.append_message(
        telegram_user.username,
        "default",  # chatgpt_role
        thread_id,
        "assistant",  # speaker_role
        answer,
    )

    # send user response back
    for i in range(0, len(answer), TELEGRAM_MSG_MAX_LEN):
        chunk = answer[i : i + TELEGRAM_MSG_MAX_LEN]
        await update.message.reply_text(chunk)


def main():
    # database init
    init_db()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", reset_command))
    # regular messages
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # launch long pollin
    app.run_polling()


if __name__ == "__main__":
    main()
