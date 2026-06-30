from pydantic import BaseModel, Field

from db.models import TelegramMessage, UserInterest

from .base_tool import BaseTool, ToolResult


class SaveInterestArgs(BaseModel):
    short_info: str = Field(
        ...,
        max_length=128,
        description="Brief label for what the user wants now (e.g. 'Samsung S25, 256GB, black, ~8M UZS')",
    )
    status_description: str = Field(
        ...,
        description=(
            "Full picture: phone model/family, storage, RAM, color, budget, use-case. "
            "Write enough so future turns can resume without re-reading the chat."
        ),
    )
    message_id: int | None = Field(
        None,
        description="Telegram message_id where this interest started. Omit if unknown.",
    )


class SaveInterest(BaseTool):
    name = "save_interest"
    description = (
        "Call this every time the user changes what they want — whether it's a completely new "
        "product/brand or a technical change (storage, RAM, color, budget). Always creates a new "
        "entry; never updates an old one. This keeps a full history of the user's decisions."
    )
    args_model = SaveInterestArgs

    async def run(self, args: SaveInterestArgs) -> ToolResult:
        if self.ctx.user_id is None:
            return ToolResult(content="No user context.", is_error=True)

        msg = None
        if args.message_id is not None:
            msg = await TelegramMessage.filter(
                user_id=self.ctx.user_id, message_id=args.message_id
            ).first()

        interest = await UserInterest.create(
            user_id=self.ctx.user_id,
            telegram_message=msg,
            short_info=args.short_info,
            status_description=args.status_description,
        )
        return ToolResult(
            content=f"Interest saved (id={interest.id}): {args.short_info}",
            data={"id": interest.id},
        )
