from telegram import Update
from telegram.ext import ContextTypes

from app.config.logging import logger
from app.services import history_service, user_role_allowed


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /reset handler
    """
    user_cache = context.application.bot_data["user_cache"]
    user_repo = context.application.bot_data["user_repo"]

    telegram_user = user_cache.get_or_create(update)

    thread_id = 0
    chatgpt_role = "default"

    if not user_role_allowed(telegram_user, user_repo):
        await update.message.reply_text("⛔ You have no access to /reset in this bot.")
        logger.info(
            "User %s was restricted from using /reset command.", telegram_user.username
        )
        return

    history_service.reset_history(
        username=telegram_user.username,
        chatgpt_role=chatgpt_role,
        thread_id=0,
    )

    reply_text = (
        "Your chat history has been deleted.\n\n"
        f"User = {telegram_user.username}\n"
        f"ChatGPT role = {chatgpt_role}\n"
        f"Thread_id = {thread_id}\n"
    )

    await update.message.reply_text(reply_text)
