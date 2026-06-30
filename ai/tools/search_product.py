from typing import Any

from pydantic import BaseModel, Field
from tortoise.expressions import Q

from db.models import Phone
from .base_tool import BaseTool, ToolResult


class SearchPhoneArgs(BaseModel):
    name__contains: list[str] = Field(None, description="Filter by phone name (partial match, OR-ed)")
    brand__contains: list[str] = Field(None, description="Filter by brand name (partial match, OR-ed)")
    price__gte: int | None = Field(None, description="Minimum price in UZS (inclusive)")
    price__lte: int | None = Field(None, description="Maximum price in UZS (inclusive)")
    rom__contains: list[int] = Field(None, description="Required storage options in GB (phone must have at least one)")
    ram__contains: list[int] = Field(None, description="Required RAM options in GB (phone must have at least one)")
    color__contains: str | None = Field(None, description="Filter by available color (partial match)")
    sort_fields: list[str] = Field(None, description="Sorting fields with priority order. Prefix - for descending. Regular fields: price, name, brand_id. Array fields sorted by max value: rom_options, ram_options. Example: ['-rom_options', 'price']")


class SearchPhone(BaseTool):
    name = "search_phone"
    description = (
        "Search the store inventory for phones. Call this for any question about a specific "
        "phone, brand, price range, storage, RAM, or color. Always search instead of relying "
        "on assumed knowledge."
    )
    args_model = SearchPhoneArgs

    async def run(self, args: SearchPhoneArgs) -> ToolResult:
        q = Q()
        scalar_filters: dict[str, Any] = {}

        if args.name__contains:
            name_q = Q()
            for term in args.name__contains:
                name_q |= Q(name__icontains=term)
            q &= name_q

        if args.brand__contains:
            brand_q = Q()
            for term in args.brand__contains:
                brand_q |= Q(brand_id__icontains=term)
            q &= brand_q

        if args.price__gte is not None:
            scalar_filters["price__gte"] = args.price__gte
        if args.price__lte is not None:
            scalar_filters["price__lte"] = args.price__lte

        _ARRAY_FIELDS = {"rom_options", "ram_options"}
        orm_sort = [f for f in (args.sort_fields or []) if f.lstrip("-") not in _ARRAY_FIELDS]
        py_sort = [f for f in (args.sort_fields or []) if f.lstrip("-") in _ARRAY_FIELDS]

        qs = Phone.filter(q, **scalar_filters)
        if orm_sort:
            qs = qs.order_by(*orm_sort)
        phones = await qs

        if args.rom__contains:
            phones = [p for p in phones if any(r in p.rom_options for r in args.rom__contains)]
        if args.ram__contains:
            phones = [p for p in phones if any(r in p.ram_options for r in args.ram__contains)]
        if args.color__contains:
            needle = args.color__contains.lower()
            phones = [p for p in phones if any(needle in c.lower() for c in p.colors)]

        for field in reversed(py_sort):
            desc = field.startswith("-")
            attr = field.lstrip("-")
            phones.sort(key=lambda p: max(getattr(p, attr), default=0), reverse=desc)

        if not phones:
            return ToolResult(content="No phones found matching your criteria.", data={"phones": []})

        data_phones = []
        for p in phones:
            data_phones.append({
                "id": p.id,
                "name": p.name,
                "brand": p.brand_id,
                "price": p.price,
                "rom_options": p.rom_options,
                "ram_options": p.ram_options,
                "colors": p.colors,
                "buy_link": p.buy_link,
            })

        return ToolResult(
            content=f"Found {len(phones)} phone(s): {data_phones[:10]}",
        )
