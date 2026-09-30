from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.utils.permissions import is_owner


class IsOwner(BaseFilter):
    """فقط مالک/مالکین ربات."""

    async def __call__(self, message: Message) -> bool:
        return message.from_user is not None and is_owner(message.from_user.id)
