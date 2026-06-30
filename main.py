import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from ai.client import AIClient
from bot.handlers import chat
from config import load_config
from db.init import close_db, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()

    await init_db(config.database_url)
    logger.info("Database connected.")

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    ai_client = AIClient(
        api_key=config.anthropic_api_key,
        model=config.claude_model,
        max_history=config.max_history_messages,
    )
    await ai_client.initialize()

    dp = Dispatcher()
    dp["ai_client"] = ai_client

    dp.include_router(chat.router)

    logger.info("Starting TechPhone Store bot...")
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await close_db()
        logger.info("Database disconnected.")


if __name__ == "__main__":
    asyncio.run(main())
