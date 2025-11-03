from telegram import Update
from telegram.ext import ContextTypes

from app.config import logger, settings
from app.services import history_service, user_role_allowed
from app.services.gpt_service import ask_gpt


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    forward default message to GPT and return response
    """
    user_cache = context.application.bot_data["user_cache"]
    user_repo = context.application.bot_data["user_repo"]

    telegram_user = user_cache.get_or_create(update)
    if not user_role_allowed(telegram_user, user_repo):
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
    history_service.append_message(
        telegram_user.username,
        "default",  # chatgpt_role
        thread_id,
        "user",  # speaker_role
        user_text,
    )

    # get chat history + user input
    user_text_and_context = history_service.get_recent_history(
        telegram_user.username, chatgpt_role="default", thread_id=0
    )

    # call OpenAI model
    answer = ask_gpt(user_text_and_context)

    # add OpenAI answer to chat history
    history_service.append_message(
        telegram_user.username,
        "default",  # chatgpt_role
        thread_id,
        "assistant",  # speaker_role
        answer,
    )

    # send user response back
    for i in range(0, len(answer), settings.telegram_msg_max_len):
        chunk = answer[i : i + settings.telegram_msg_max_len]
        await update.message.reply_text(chunk)
