from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from bot.database import repository as repo

logger = logging.getLogger(__name__)


async def _captcha_watch_loop(bot: Bot) -> None:
    while True:
        try:
            expired = await repo.list_expired_captchas(datetime.utcnow())
            for pending in expired:
                try:
                    await bot.ban_chat_member(pending.group_id, pending.user_id)
                    await bot.unban_chat_member(pending.group_id, pending.user_id)
                except TelegramBadRequest:
                    pass
                try:
                    await bot.delete_message(pending.group_id, pending.message_id)
                except TelegramBadRequest:
                    pass
                await repo.delete_pending_captcha(pending.group_id, pending.user_id)
        except Exception:
            logger.exception("خطا هنگام بررسی کپچاهای منقضی شده")
        await asyncio.sleep(15)


def start_captcha_scheduler(bot: Bot) -> None:
    asyncio.create_task(_captcha_watch_loop(bot))
