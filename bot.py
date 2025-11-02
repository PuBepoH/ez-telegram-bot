from typing import Dict

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import history_store
from config import (
    ALLOWED_ROLES,
    OPENAI_MODEL,
    TELEGRAM_BOT_TOKEN,
    logger,
    openai_client,
)
from db_init import init_db
from user_repo import TelegramUserData, UserRepo

telegram_users_by_tg_id: Dict[int, TelegramUserData] = {}
user_repo = UserRepo()
TELEGRAM_MSG_MAX_LEN = 4000  # Telegram has msg length limit for ~4096 symbols


def get_or_create_telegram_user_info(update: Update) -> TelegramUserData:
    """
    Get TelegramUserData for this update
    If there are not such user in memory - create and append to telegram_users_dict
    """
    effective_user = update.effective_user
    tg_id = effective_user.id

    # if user already presented in telegram_users_by_tg_id => update data and return
    if tg_id in telegram_users_by_tg_id:
        u = telegram_users_by_tg_id[tg_id]
        # update dynamic fiels, ppl can change username, first name and last name
        u.username = effective_user.username or f"user_{tg_id}"
        u.first_name = effective_user.first_name
        u.last_name = effective_user.last_name
        return u

    # if user is not presented in telegram_users_by_tg_id => create new record
    new_user = TelegramUserData(
        tg_id=tg_id,
        username=effective_user.username or f"user_{tg_id}",
        first_name=effective_user.first_name,
        last_name=effective_user.last_name,
    )
    telegram_users_by_tg_id[tg_id] = new_user
    return new_user


def user_role_allowed(telegram_user: TelegramUserData) -> bool:
    role = user_repo.upsert_and_get_role(
        telegram_user,
    )
    logger.info("User %s have %s role", telegram_user.username, role)
    return role in ALLOWED_ROLES


# ---------- function for communication with GPT ----------
def ask_gpt(user_text_and_context: list[dict[str, str]]) -> str:
    """
    Send user text to OpenAI and return response
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
    Welcome user and return his role in system
    """
    telegram_user = get_or_create_telegram_user_info(update)
    role = user_repo.upsert_and_get_role(telegram_user)

    reply_text = (
        "Hello, I'm ezBot!\n\n"
        "I can send requests to ChatGPT and return responses.\n\n"
        f"Your username is: {telegram_user.username}\n"
        f"Your telegram_id is: {telegram_user.tg_id}\n"
        f"Your role is: {role}\n"
    )

    await update.message.reply_text(reply_text)


async def add_command(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    /add <telegram_id>

    Admin-only feature
    Apply role 'user' to user with <telegram_id>
    """
    telegram_user = get_or_create_telegram_user_info(update)
    user_role = user_repo.get_role(telegram_user.tg_id)
    if user_role != "admin":
        await update.message.reply_text("⛔ You have no access to /add in this bot.")
        logger.info(
            "User %s was restricted from using /admin command (role=%s).",
            telegram_user.username,
            user_role,
        )
        return

    text = update.message.text or ""
    parts = text.strip().split()

    # check command syntax
    if len(parts) != 2:
        await update.message.reply_text(
            "❗ Usage: /add <telegram_id>\nExample: /add 123456789"
        )
        return

    # check argument type
    target_tg_id_raw = parts[1]
    try:
        target_tg_id = int(target_tg_id_raw)
    except ValueError:
        await update.message.reply_text(
            f"❗ '{target_tg_id_raw}' is not a valid telegram_id (must be integer)."
        )
        return

    user_repo.set_role(target_tg_id, "user")

    await update.message.reply_text(
        f"✅ User with telegram_id={target_tg_id} has now role 'user'."
    )

    logger.info(
        "Admin %s (%s) set role 'user' for telegram_id=%s",
        telegram_user.username,
        telegram_user.tg_id,
        target_tg_id,
    )


async def reset_command(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    /reset handler
    """
    telegram_user = get_or_create_telegram_user_info(update)

    thread_id = 0

    if not user_role_allowed(telegram_user):
        await update.message.reply_text("⛔ You have no access to /reset in this bot.")
        logger.info(
            "User %s was restricted from using /reset command.", telegram_user.username
        )
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
    telegram_user = get_or_create_telegram_user_info(update)
    if not user_role_allowed(telegram_user):
        await update.message.reply_text(
            "⛔ You have no access to message ChatGPT in this bot."
        )
        return

    user_text = update.message.text
    logger.info("Got message from user %s", telegram_user.username)
    thread_id = 0

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
    app.add_handler(CommandHandler("add", reset_command))
    # regular messages
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # launch long pollin
    app.run_polling()


if __name__ == "__main__":
    main()
