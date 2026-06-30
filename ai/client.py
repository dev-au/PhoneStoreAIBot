import asyncio
import logging
from typing import Any

import anthropic

from ai.prompts import build_system_prompt
from ai.tools import TOOLS, ToolContext, execute_tool
from db.models import Brand, TelegramMessage

_MAX_TOOL_ROUNDS = 10
_SEND_TOOLS = {"send_message", "send_search_result"}

MessageHistory = list[dict[str, Any]]

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self, api_key: str, model: str, max_history: int) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_history = max_history
        self._system_prompt = build_system_prompt()

    async def initialize(self) -> None:
        brands = await Brand.all().values_list("name", flat=True)
        self._system_prompt = build_system_prompt(list(brands))

    async def send_message(
        self,
        user_message: str,
        messages: list[TelegramMessage],
        ctx: ToolContext | None = None,
    ) -> MessageHistory:
        if ctx is None:
            ctx = ToolContext()

        history = self._trim(
            self.messages_into_json(messages) + [{"role": "user", "content": user_message}]
        )

        for round_num in range(_MAX_TOOL_ROUNDS):
            logger.info(
                "Claude request  | round=%d user=%s history_len=%d msg=%.120s",
                round_num,
                ctx.user_id,
                len(history),
                user_message,
            )

            response = await self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                system=self._system_prompt,
                messages=history,
                tools=TOOLS,
                tool_choice={"type": "any"},
            )

            tool_blocks = [b for b in response.content if b.type == "tool_use"]
            logger.info(
                "Claude response | round=%d user=%s stop=%s in=%d out=%d tools=%s",
                round_num,
                ctx.user_id,
                response.stop_reason,
                response.usage.input_tokens,
                response.usage.output_tokens,
                [b.name for b in tool_blocks],
            )
            for block in tool_blocks:
                logger.info("  -> tool_call | %s args=%s", block.name, block.input)

            history = history + [{"role": "assistant", "content": response.content}]

            results = await asyncio.gather(
                *[execute_tool(b.name, b.input, ctx) for b in tool_blocks]
            )
            for block, result in zip(tool_blocks, results):
                logger.info("  <- tool_result | %s result=%.200s", block.name, result)

            tool_results = [
                {"type": "tool_result", "tool_use_id": b.id, "content": r}
                for b, r in zip(tool_blocks, results)
            ]
            history = history + [{"role": "user", "content": tool_results}]

            if any(b.name in _SEND_TOOLS for b in tool_blocks):
                break

        return history

    def _trim(self, history: MessageHistory) -> MessageHistory:
        if len(history) <= self._max_history:
            return history
        trimmed = history[len(history) - self._max_history :]
        while trimmed and (
            trimmed[0]["role"] != "user" or isinstance(trimmed[0]["content"], list)
        ):
            trimmed = trimmed[1:]
        return trimmed

    def messages_into_json(self, messages: list[TelegramMessage]) -> MessageHistory:
        return [msg.into_json() for msg in messages]
