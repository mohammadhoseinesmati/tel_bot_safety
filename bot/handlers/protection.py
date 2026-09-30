from __future__ import annotations

import asyncio
import re
import time
from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from bot.database import repository as repo
from bot.utils.permissions import RESTRICTED_PERMISSIONS, is_group_admin

router = Router(name="protection")

URL_PATTERN = re.compile(r"(https?://\S+|t\.me/\S+|telegram\.me/\S+|www\.\S+)", re.IGNORECASE)
USERNAME_PATTERN = re.compile(r"@\w{4,}")

# (chat_id, user_id) -> list of message timestamps (monotonic seconds)
_flood_tracker: dict[tuple[int, int], list[float]] = {}


def _check_flood(chat_id: int, user_id: int, limit: int, window: int) -> bool:
    key = (chat_id, user_id)
    now = time.monotonic()
    timestamps = _flood_tracker.setdefault(key, [])
    timestamps.append(now)
    timestamps[:] = [t for t in timestamps if now - t <= window]
    if len(timestamps) > limit:
        _flood_tracker[key] = []
        return True
    return False


async def _apply_action(bot: Bot, chat_id: int, user_id: int, action: str, minutes: int | None = None) -> None:
    try:
        if action == "ban":
            await bot.ban_chat_member(chat_id, user_id)
        elif action == "kick":
            await bot.ban_chat_member(chat_id, user_id)
            await bot.unban_chat_member(chat_id, user_id)
        else:
            until = datetime.utcnow() + timedelta(minutes=minutes or 60)
            await bot.restrict_chat_member(chat_id, user_id, RESTRICTED_PERMISSIONS, until_date=until)
    except TelegramBadRequest:
        pass


async def _auto_delete(message: Message, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


@router.message(F.chat.type.in_({"group", "supergroup"}), ~F.new_chat_members, ~F.left_chat_member)
async def guard_messages(message: Message, bot: Bot) -> None:
    if message.from_user is None or message.from_user.is_bot:
        return

    if await is_group_admin(bot, message.chat.id, message.from_user.id):
        return

    group = await repo.get_or_create_group(message.chat.id, message.chat.title, message.from_user.id)
    text = message.text or message.caption or ""

    violated_lock = None
    if group.lock_links and URL_PATTERN.search(text):
        violated_lock = "لینک"
    elif group.lock_usernames and USERNAME_PATTERN.search(text):
        violated_lock = "یوزرنیم"
    elif group.lock_forward and message.forward_origin is not None:
        violated_lock = "فوروارد"
    elif group.lock_photo and message.photo:
        violated_lock = "عکس"
    elif group.lock_video and message.video:
        violated_lock = "ویدیو"
    elif group.lock_sticker and message.sticker:
        violated_lock = "استیکر"

    if violated_lock:
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        warning = await bot.send_message(message.chat.id, f"🚫 ارسال {violated_lock} در این گروه مجاز نیست.")
        asyncio.create_task(_auto_delete(warning, 5))
        return

    if group.bad_words_filter and text:
        bad_words = await repo.list_bad_words(message.chat.id)
        if bad_words:
            lowered = text.lower()
            if any(word in lowered for word in bad_words):
                try:
                    await message.delete()
                except TelegramBadRequest:
                    pass
                count = await repo.add_warning(message.chat.id, message.from_user.id)
                warning = await bot.send_message(
                    message.chat.id,
                    f"🚫 استفاده از کلمات نامناسب مجاز نیست. اخطار: {count}/{group.warn_limit}",
                )
                asyncio.create_task(_auto_delete(warning, 5))
                if count >= group.warn_limit:
                    await repo.reset_warning(message.chat.id, message.from_user.id)
                    await _apply_action(bot, message.chat.id, message.from_user.id, group.warn_action)
                return

    if group.anti_flood and _check_flood(
        message.chat.id, message.from_user.id, group.flood_limit, group.flood_seconds
    ):
        await _apply_action(bot, message.chat.id, message.from_user.id, group.flood_action, minutes=10)
        await bot.send_message(
            message.chat.id,
            f"⚡️ کاربر {message.from_user.full_name} به دلیل ارسال پیام بیش از حد مجاز محدود شد.",
        )
