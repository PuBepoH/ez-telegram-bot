from telegram import Update
from telegram.ext import ContextTypes

from app.config.logging import logger


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /add <telegram_id>

    Admin-only feature
    Apply role 'user' to user with <telegram_id>
    """
    user_cache = context.application.bot_data["user_cache"]
    user_repo = context.application.bot_data["user_repo"]

    telegram_user = user_cache.get_or_create(update)

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
