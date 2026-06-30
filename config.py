import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    anthropic_api_key: str
    database_url: str
    claude_model: str
    max_history_messages: int


def _build_database_url() -> str:
    user = os.getenv("POSTGRES_USER", "")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "")
    return f"postgres://{user}:{password}@{host}:{port}/{db}"


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    if not bot_token:
        raise ValueError("BOT_TOKEN is not set")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set")

    return Config(
        bot_token=bot_token,
        anthropic_api_key=anthropic_api_key,
        database_url=_build_database_url(),
        claude_model=os.getenv("CLAUDE_MODEL", "claude-opus-4-8"),
        max_history_messages=int(os.getenv("MAX_HISTORY_MESSAGES", "20")),
    )
