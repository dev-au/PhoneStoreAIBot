# PhoneStoreAIBot

AI-powered Telegram sales assistant for **TechPhone Store** — a phone retailer in Uzbekistan. The bot helps customers search inventory, compare phones, and tracks their interests across sessions. Replies in Uzbek, Russian, or English depending on the user.

## Stack

- **Python 3.12** · [aiogram 3](https://docs.aiogram.dev/) · [Anthropic Claude](https://docs.anthropic.com/)
- **Tortoise ORM** + asyncpg · PostgreSQL
- **Docker Compose** · [uv](https://github.com/astral-sh/uv) · ruff

## Features

- Natural-language phone search with filters (brand, price, RAM, ROM, color, sorting)
- Sends results directly via Telegram — Claude never returns plain text, only uses tools
- Per-user interest history: every search saves what the user wanted so context survives across sessions
- Brands loaded from DB into the system prompt at startup

## Project Structure

```
ai/
  client.py          # AIClient — tool-only loop, logging
  prompts.py         # System prompt with brand injection
  tools/
    search_product.py  # search_phone — filters + sorting
    send_message.py    # send_message, send_search_result → Telegram
    fetch_history.py   # fetch_messages
    user_interest.py   # list_interest, get_interest
    track_interst.py   # save_interest
    base_tool.py       # BaseTool, ToolContext, ToolResult
bot/
  handlers/chat.py   # Message handler — saves to DB, fetches history, calls AI
db/
  models.py          # TelegramMessage, UserInterest, Brand, Phone
  init.py            # Tortoise init + aerich config
config.py            # Loads config from env vars
seed.py              # Seeds DB from train_test_data.py
```

## Setup

### 1. Environment

```bash
cp .env.example .env
# Fill in BOT_TOKEN and ANTHROPIC_API_KEY
```

`.env` variables:

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram bot token |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `POSTGRES_USER` | DB user |
| `POSTGRES_PASSWORD` | DB password |
| `POSTGRES_DB` | DB name |
| `POSTGRES_HOST` | DB host (default: `db`) |
| `POSTGRES_PORT` | DB port (default: `5432`) |
| `CLAUDE_MODEL` | Model ID (default: `claude-opus-4-8`) |
| `MAX_HISTORY_MESSAGES` | Trimmed history size (default: `20`) |

### 2. Run

```bash
docker-compose up --build
```

### 3. Seed the database

```bash
uv run python seed.py
```

Loads brands and phones from `train_test_data.py`. Safe to re-run (uses `get_or_create`).

## Development

```bash
uv sync
uv run ruff check .
uv run ruff check --fix .
```
