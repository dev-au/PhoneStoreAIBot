from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

from pydantic import BaseModel


@dataclass
class ToolContext:
    bot: Any = None
    database: Any = None
    user_id: int | None = None


@dataclass
class ToolResult:
    content: str
    data: dict[str, Any] | None = None
    is_error: bool = False


class BaseTool(ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    args_model: ClassVar[type[BaseModel]]

    def __init__(self, ctx: ToolContext) -> None:
        self.ctx = ctx

    @abstractmethod
    async def run(self, args: BaseModel) -> ToolResult: ...
