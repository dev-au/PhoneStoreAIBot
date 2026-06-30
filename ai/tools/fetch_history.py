
from pydantic import BaseModel, Field

from db.models import TelegramMessage

from .base_tool import BaseTool, ToolResult


class FetchMessageArgs(BaseModel):
    count: int = Field(
        description="Number of recent messages to fetch from chat history", le=20
    )
    start_from: int | None = Field(
        description="When user replied too old message, give this message_id and get old conversation"
    )


class FetchMessage(BaseTool):
    name = "fetch_messages"
    description = "Fetch the most recent chat messages for the current user"
    args_model = FetchMessageArgs

    async def run(self, args: FetchMessageArgs) -> ToolResult:
        if self.ctx.user_id is None:
            return ToolResult(content="No user context available.", is_error=True)

        if args.start_from is None:
            messages = (
                await TelegramMessage.filter(user_id=self.ctx.user_id)
                .order_by("-created_at")
                .limit(args.count)
            )
        else:
            messages = (
                await TelegramMessage.filter(
                    user_id=self.ctx.user_id, message_id__lte=args.start_from
                )
                .order_by("-created_at")
                .limit(args.count)
            )

        if not messages:
            return ToolResult(content="No messages found.", data={"messages": []})

        messages = list(reversed(messages))
        formatted = [f"[{m.role}] {m.content}" for m in messages]
        return ToolResult(
            content="\n".join(formatted),
            data={
                "messages": [{"role": m.role, "content": m.content} for m in messages]
            },
        )
