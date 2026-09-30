from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.utils.permissions import is_group_admin


class IsGroupAdmin(BaseFilter):
    """فقط ادمین‌های گروه (یا مالک ربات) اجازه اجرای دستور را دارند."""

    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False
        return await is_group_admin(message.bot, message.chat.id, message.from_user.id)
