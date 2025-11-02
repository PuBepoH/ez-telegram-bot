from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import history_store
from config import OPENAI_MODEL, TELEGRAM_BOT_TOKEN, openai_client

TELEGRAM_MSG_MAX_LEN = 4000  # Telegram has msg length limit for ~4096 symbols


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


async def handle_message(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    forward default message to GPT and return response
    """
    user = update.effective_user

    username = user.username or f"user_{user.id}"
    thread_id = 0
    user_text = update.message.text

    if not user_text or user_text.strip() == "":
        await update.message.reply_test(
            "Мне нужен текст запроса. Не могу отправить пустой"
        )
        return

    # add user input to chat history
    history_store.append_message(
        username,
        "default",  # chatgpt_role
        thread_id,
        "user",  # speaker_role
        user_text,
    )

    # get chat history + user input
    user_text_and_context = history_store.get_recent_history(
        username, chatgpt_role="default", thread_id=0
    )

    # call OpenAI model
    answer = ask_gpt(user_text_and_context)

    # add OpenAI answer to chat history
    history_store.append_message(
        username,
        "default",  # chatgpt_role
        thread_id,
        "assistant",  # speaker_role
        user_text,
    )

    # send user response back
    for i in range(0, len(answer), TELEGRAM_MSG_MAX_LEN):
        chunk = answer[i : i + TELEGRAM_MSG_MAX_LEN]
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
