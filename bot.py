import history_store
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)
from config import TELEGRAM_BOT_TOKEN, OPENAI_MODEL, openai_client


# ---------- function for communication with GPT ----------
def ask_gpt(user_message: str) -> str:
    """
    send user text to OpenAI and return response
    """
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "Ты — дружелюбный помощник. Отвечай кратко и по делу."},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
    )

    answer = response.choices[0].message.content
    return answer.strip()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start handler
    """
    await update.message.reply_text(
        "Привет, я ezBot! Я могу отправлять твои запросы к ChatGPT и возвращать ответы. Погнали?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    forward default message to GPT and return response
    """
    user = update.effective_user

    username = user.username or f"user_{user.id}"
    #thread_id = 0
    user_text = update.message.text

    if not user_text or user_text.strip() == "":
        await update.message.reply_test("Мне нужен текст запроса. Не могу отправить пустой")
        return
    
    # add user input to chat history
    history_store.append_message(username, chatgpt_role="default", thread_id = 0)

    # get chat history + user input
    user_text_and_context = history_store.get_recent_history(username, chatgpt_role= "default", thread_id = 0)

    # call OpenAI model
    answer = ask_gpt(user_text_and_context)

    # add OpenAI answer to chat history
    history_store.append_message()
    
    MAX_LEN = 4000 # Telegram has msg length limit for ~4096 symbols

    # send user response back
    for i in range(0, len(answer), MAX_LEN):
        chunk = answer[i : i + MAX_LEN]
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