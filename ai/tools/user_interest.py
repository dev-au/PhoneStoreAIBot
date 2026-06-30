from pydantic import BaseModel, Field

from db.models import UserInterest

from .base_tool import BaseTool, ToolResult


class _NoArgs(BaseModel):
    pass


class ListUserInterest(BaseTool):
    name = "list_interest"
    description = (
        "List all recorded interests for the current user. "
        "Returns id + short_info only — use get_interest to fetch full details of one."
    )
    args_model = _NoArgs

    async def run(self, args: _NoArgs) -> ToolResult:
        if self.ctx.user_id is None:
            return ToolResult(content="No user context.", is_error=True)

        interests = (
            await UserInterest.filter(user_id=self.ctx.user_id)
            .order_by("-created_at")
            .values("id", "short_info", "created_at")
        )
        if not interests:
            return ToolResult(content="No interests recorded yet.", data={"interests": []})

        lines = [f"[{i['id']}] {i['short_info']}" for i in interests]
        return ToolResult(content="\n".join(lines), data={"interests": list(interests)})


class FetchUserInterestArgs(BaseModel):
    interest_id: int = Field(
        ..., description="Interest id to fetch. Pass -1 to get the latest."
    )


class FetchUserInterest(BaseTool):
    name = "get_interest"
    description = (
        "Fetch full details of a specific interest (short_info + status_description). "
        "Pass -1 to get the latest one and resume context from a previous session."
    )
    args_model = FetchUserInterestArgs

    async def run(self, args: FetchUserInterestArgs) -> ToolResult:
        if self.ctx.user_id is None:
            return ToolResult(content="No user context.", is_error=True)

        qs = UserInterest.filter(user_id=self.ctx.user_id)
        interest = (
            await qs.order_by("-created_at").first()
            if args.interest_id == -1
            else await qs.filter(id=args.interest_id).first()
        )
        if interest is None:
            return ToolResult(content="No interest found.", is_error=True)

        return ToolResult(
            content=f"[{interest.id}] {interest.short_info}\n{interest.status_description}",
            data={
                "id": interest.id,
                "short_info": interest.short_info,
                "status_description": interest.status_description,
                "created_at": str(interest.created_at),
            },
        )
