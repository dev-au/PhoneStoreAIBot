from __future__ import annotations

from enum import StrEnum
from typing import Any

from tortoise import fields
from tortoise.contrib.postgres.fields import ArrayField
from tortoise.models import Model


class TelegramMessage(Model):
    user_id = fields.BigIntField()
    message_id = fields.BigIntField()
    role = fields.CharEnumField(
        enum_type=StrEnum("Role", {"user": "user", "assistant": "assistant"})
    )
    created_at = fields.DatetimeField()
    content = fields.TextField()

    @classmethod
    async def get_latest_conversations(cls, user_id: int) -> list[TelegramMessage]:
        latest_interest = (
            await UserInterest.filter(user_id=user_id).order_by("-created_at").first()
        )
        if latest_interest is None:
            return await cls.filter(user_id=user_id).order_by("created_at")
        pivot_msg = await latest_interest.telegram_message
        if pivot_msg is None:
            return await cls.filter(user_id=user_id).order_by("created_at")
        return await cls.filter(
            user_id=user_id, created_at__gte=pivot_msg.created_at
        ).order_by("created_at")
    
    def into_json(self) -> dict[str, Any]:
        return {"role": self.role, "content": self.content}


class UserInterest(Model):
    user_id = fields.BigIntField()
    telegram_message = fields.ForeignKeyField(
        "models.TelegramMessage", related_name="user_interests", null=True
    )
    short_info = fields.CharField(max_length=128)
    status_description = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)


class Brand(Model):
    name = fields.CharField(primary_key=True, max_length=64)


class Phone(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=128)
    brand = fields.ForeignKeyField(
        "models.Brand", related_name="phones", to_field="name"
    )
    price = fields.IntField()
    rom_options = ArrayField("INT", default=[])
    ram_options = ArrayField("INT", default=[])
    colors = ArrayField("VARCHAR(64)", default=[])
    buy_link = fields.TextField()

    class Meta:
        table = "phones"

    def __str__(self) -> str:
        return f"{self.name} ({self.brand_id})"
