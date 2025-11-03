from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.handlers.add_handler import add_command
from app.handlers.message_handler import handle_message
from app.handlers.reset_handler import reset_command
from app.handlers.start_handler import start_command


def register_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
