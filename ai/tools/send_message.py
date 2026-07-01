
from pydantic import BaseModel, Field

from db.models import Phone, TelegramMessage

from .base_tool import BaseTool, ToolResult


class SendMessageArgs(BaseModel):
    text: str = Field(..., description="Message text to send to the user (Markdown supported)", max_length=2048)


class SendMessage(BaseTool):
    name = "send_message"
    description = (
        "Send a text message directly to the user in Telegram. "
        "Use for clarifying questions, short answers, or any reply that isn't a phone list."
    )
    args_model = SendMessageArgs

    async def run(self, args: SendMessageArgs) -> ToolResult:
        return await self._send(args.text)

    async def _send(self, text: str) -> ToolResult:
        if self.ctx.bot is None or self.ctx.user_id is None:
            return ToolResult(content="No bot/user context.", is_error=True)

        sent = await self.ctx.bot.send_message(
            chat_id=self.ctx.user_id,
            text=text,
            parse_mode="Markdown",
        )

        await TelegramMessage.create(
            user_id=self.ctx.user_id,
            message_id=sent.message_id,
            role="assistant",
            created_at=sent.date,
            content=text,
        )

        return ToolResult(content="sent", data={"message_id": sent.message_id})


class SendSearchResultArgs(BaseModel):
    id_list: list[int] = Field(
        ..., description="Ordered list of phone IDs that best match the user's request (best first)"
    )
    extra_text: str = Field(
        ...,
        description=(
            "Sales note shown after the list — mention a key benefit, suggest a step-up model, "
            "or invite the user to narrow down further."
        ),
    )


class SendSearchResult(SendMessage):
    name = "send_search_result"
    description = (
        "After calling search_phone, pick the best matching IDs and call this to send a clean, "
        "link-ready list directly to the user. Use extra_text for a helpful nudge or comparison note."
    )
    args_model = SendSearchResultArgs

    async def run(self, args: SendSearchResultArgs) -> ToolResult:
        phones = await Phone.filter(id__in=args.id_list)
        order = {pid: i for i, pid in enumerate(args.id_list)}
        phones.sort(key=lambda p: order.get(p.id, 999))

        lines = []
        for p in phones:
            specs = []
            if p.ram_options:
                specs.append(f"RAM: {'/'.join(str(v) for v in p.ram_options)} GB")
            if p.rom_options:
                specs.append(f"ROM: {'/'.join(str(v) for v in p.rom_options)} GB")
            if p.colors:
                specs.append(f"Colors: {', '.join(p.colors)}")
            specs_line = f"\n  {' | '.join(specs)}" if specs else ""
            lines.append(
                f"• *{p.name}* ({p.brand_id}) — {p.price:,} UZS{specs_line}\n  {p.buy_link}"
            )
        text = "\n\n".join(lines)
        if args.extra_text:
            text += f"\n\n{args.extra_text}"

        return await self._send(text)
