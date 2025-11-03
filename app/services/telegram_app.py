from typing import Any

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import logger, settings
from app.handlers import add_command, handle_message, reset_command, start_command
from app.handlers.errors import error_handler


class TelegramApp:
    def __init__(self) -> None:
        self.app: Application = (
            ApplicationBuilder().token(settings.telegram_bot_token).build()
        )

    def with_dependencies(self, **deps: Any) -> "TelegramApp":
        """
        Save dependencies in application.bot_data
        """
        self.app.bot_data.update(deps)
        return self

    def register(self) -> "TelegramApp":
        self.app.add_handler(CommandHandler("start", start_command))
        self.app.add_handler(CommandHandler("reset", reset_command))
        self.app.add_handler(CommandHandler("add", add_command))
        self.app.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
        )
        self.app.add_error_handler(error_handler)
        logger.info("Handlers registered")
        return self

    def run(self) -> None:
        logger.info("Starting polling Telegram for updates...")
        self.app.run_polling()
