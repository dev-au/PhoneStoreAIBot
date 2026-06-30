from .base_tool import BaseTool, ToolContext
from .fetch_history import FetchMessage
from .search_product import SearchPhone
from .send_message import SendMessage, SendSearchResult
from .track_interst import SaveInterest
from .user_interest import FetchUserInterest, ListUserInterest

_REGISTRY: dict[str, type[BaseTool]] = {
    FetchMessage.name: FetchMessage,
    SearchPhone.name: SearchPhone,
    SendMessage.name: SendMessage,
    SendSearchResult.name: SendSearchResult,
    SaveInterest.name: SaveInterest,
    ListUserInterest.name: ListUserInterest,
    FetchUserInterest.name: FetchUserInterest,
}


def _build_tools_schema() -> list[dict]:
    result = []
    for tool_cls in _REGISTRY.values():
        schema = tool_cls.args_model.model_json_schema()
        schema.pop("title", None)
        result.append(
            {
                "name": tool_cls.name,
                "description": tool_cls.description,
                "input_schema": schema,
            }
        )
    return result


TOOLS: list[dict] = _build_tools_schema()


async def execute_tool(name: str, args: dict, ctx: ToolContext) -> str:
    tool_cls = _REGISTRY.get(name)
    if tool_cls is None:
        return f"Unknown tool: {name}"
    tool = tool_cls(ctx)
    parsed = tool_cls.args_model(**args)
    result = await tool.run(parsed)
    return result.content
