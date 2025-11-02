# ez-telegram-bot

A simple Telegram bot that connects to the OpenAI API (ChatGPT) and returns model responses directly to Telegram messages.

## ✨ Features

- `/start` — greeting message  
- Any text message — forwarded to the OpenAI model and the reply is sent back  
- Automatic proxy sanitization — removes unsupported SOCKS proxies from environment variables to prevent `httpx` crashes  
- Environment-based configuration via `.env` file  

---

## Requirements

- Python 3.12+
- A Telegram account with a created bot via @BotFather
- An OpenAI API key from platform.openai.com
- Redis database

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/PuBepoH/ez-telegram-bot.git
cd ez-telegram-bot
```

### 2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env

# edit .env as follow
TELEGRAM_BOT_TOKEN=your_bot_token_from_BotFather
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
```

### 5. Run the bot
```bash
python bot.py
```
