from aiogram import Router
from aiogram.types import Message

from ai.client import AIClient
from ai.tools import ToolContext
from db.models import TelegramMessage

router = Router()

@router.message()
async def handle_message(message: Message, ai_client: AIClient) -> None:

    user_id = message.from_user.id if message.from_user else None
    if user_id is None:
        return

    await TelegramMessage.create(
        user_id=user_id,
        message_id=message.message_id,
        role="user",
        created_at=message.date,
        content=message.text,
    )

    history = await TelegramMessage.get_latest_conversations(user_id)

    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        ctx = ToolContext(bot=message.bot, user_id=user_id)
        await ai_client.send_message(message.text, history, ctx)
    except Exception as e:
        await message.answer(
            "⚠️ Sorry, I ran into an issue processing your request. "
            "Please try again in a moment.",
        )
        raise e
