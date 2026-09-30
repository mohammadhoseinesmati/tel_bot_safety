from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.enums import ChatMemberStatus
from aiogram.types import Message

from bot.config import config
from bot.database import repository as repo
from bot.keyboards.inline import join_channels_keyboard


class ForceSubscribeMiddleware(BaseMiddleware):
    """قبل از استفاده از ربات در چت خصوصی، عضویت در کانال‌های اجباری را بررسی می‌کند."""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if event.chat.type != "private" or event.from_user is None:
            return await handler(event, data)

        if event.from_user.id in config.owner_ids:
            return await handler(event, data)

        channels = await repo.list_force_sub_channels()
        if not channels:
            return await handler(event, data)

        bot = data["bot"]
        not_joined = []
        for channel in channels:
            try:
                member = await bot.get_chat_member(channel.chat_id, event.from_user.id)
                if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
                    not_joined.append(channel)
            except Exception:
                not_joined.append(channel)

        if not_joined:
            await event.answer(
                "⚠️ برای استفاده از ربات ابتدا باید در کانال(های) زیر عضو شوید:",
                reply_markup=join_channels_keyboard(not_joined),
            )
            return None

        return await handler(event, data)
