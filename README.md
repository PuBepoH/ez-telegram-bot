# ez-telegram-bot

Telegram bot with modular architecture (handlers / services / db / config / models).

![python](https://img.shields.io/badge/python-3.12-blue) 
![lint](https://img.shields.io/badge/lint-black%20%7C%20isort%20%7C%20pylint-informational) 
![types](https://img.shields.io/badge/types-mypy-informational)

## 🚀 Quick start

```bash
git clone https://github.com/PuBepoH/ez-telegram-bot.git
cd ez-telegram-bot
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

## ⚙️ Environment (.env)

```env
ADMIN_USER_ID="1234567890"
TELEGRAM_BOT_TOKEN="some-telegram-token-here"
OPENAI_API_KEY="some-openapi-api-key-here"
OPENAI_MODEL="gpt-3.5-turbo"
REDIS_URL="redis://localhost:6379/0"
POSTGRES_DSN="postgresql://postgres:postgres@localhost:5432/bot"
```

## 🧱 Architecture

```
app/
  bot.py                  # entrypoint (launcher)
  handlers/               # Telegram command handlers: add_handler, errors, init, message_handler, reset_handler, start_handler
  services/               # business logic: gpt_service, user_cache, telegram_app, history_service
  db/                     # init_db, repositories (UserRepo)
  config/                 # settings + logging
  models/                 # dataclasses (TelegramUserData, ...)
```

Key ideas:
- `TelegramApp` encapsulates Application creation, handler registration, error handling, DI via `application.bot_data`.
- `UserCache` keeps in-memory Telegram users per process runtime.
- Roles/users live in PostgreSQL (`UserRepo`).

## 🛠 Dev commands

```bash
pip install -r requirements-dev.txt
black app && isort app
mypy app
pylint app
pre-commit run -a
```

## 🗃 Database

- Schema: `bot`
- Table: `bot.users` with roles and activity flags

## 🤖 Bot commands

- `/start` – greeting and role info
- `/reset` – clear chat history
- `/add <telegram_id>` – (admin-only) assign role `user`

## 📦 Dependencies

`requirements.txt`:
```txt
python-telegram-bot==20.7
openai==1.51.0
redis==7.0.1
python-dotenv==1.2.1
psycopg==3.2.12
```
