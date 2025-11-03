from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from app.config import logger


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Telegram update caused error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Что-то пошло не так. Попробуйте ещё раз."
            )
        except TelegramError:
            pass
