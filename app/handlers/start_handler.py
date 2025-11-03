from telegram import Update
from telegram.ext import ContextTypes

from app.config.logging import logger


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start handler
    Welcome user and return his role in system
    """
    user_cache = context.application.bot_data["user_cache"]
    telegram_user = user_cache.get_or_create(update)

    user_repo = context.application.bot_data["user_repo"]
    role = user_repo.upsert_and_get_role(telegram_user)

    reply_text = (
        "Hello, I'm ezBot!\n\n"
        "I can send requests to ChatGPT and return responses.\n\n"
        f"Your username is: {telegram_user.username}\n"
        f"Your telegram_id is: {telegram_user.tg_id}\n"
        f"Your role is: {role}\n"
    )

    await update.message.reply_text(reply_text)
    logger.info(
        "start: %s (%s) role=%s", telegram_user.username, telegram_user.tg_id, role
    )
