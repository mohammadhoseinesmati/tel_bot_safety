from __future__ import annotations

import random
from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import repository as repo
from bot.utils.permissions import FULL_PERMISSIONS, RESTRICTED_PERMISSIONS

router = Router(name="welcome")


@router.message(F.chat.type.in_({"group", "supergroup"}), F.new_chat_members)
async def on_new_members(message: Message, bot: Bot) -> None:
    group = await repo.get_or_create_group(message.chat.id, message.chat.title, message.from_user.id)

    for member in message.new_chat_members:
        if member.is_bot:
            continue

        if group.welcome_enabled:
            welcome_text = group.welcome_text or "👋 {name} به گروه خوش آمدید!"
            try:
                await message.answer(welcome_text.replace("{name}", member.full_name))
            except TelegramBadRequest:
                pass

        if group.captcha:
            await _start_captcha(bot, message.chat.id, member.id, member.full_name, group.captcha_timeout)


async def _start_captcha(bot: Bot, chat_id: int, user_id: int, name: str, timeout: int) -> None:
    try:
        await bot.restrict_chat_member(chat_id, user_id, RESTRICTED_PERMISSIONS)
    except TelegramBadRequest:
        return

    a, b = random.randint(1, 9), random.randint(1, 9)
    correct = str(a + b)
    options = {correct}
    while len(options) < 4:
        options.add(str(random.randint(2, 18)))
    options_list = list(options)
    random.shuffle(options_list)

    builder = InlineKeyboardBuilder()
    for option in options_list:
        builder.button(text=option, callback_data=f"captcha:{user_id}:{option}")
    builder.adjust(4)

    try:
        prompt = await bot.send_message(
            chat_id,
            f"🔒 {name} برای تایید عضویت، حاصل عبارت زیر را انتخاب کنید:\n\n"
            f"{a} + {b} = ?\n\n"
            f"⏳ در غیر این صورت ظرف {timeout} ثانیه از گروه حذف می‌شوید.",
            reply_markup=builder.as_markup(),
        )
    except TelegramBadRequest:
        return

    deadline = datetime.utcnow() + timedelta(seconds=timeout)
    await repo.create_pending_captcha(chat_id, user_id, prompt.message_id, deadline, correct)


@router.callback_query(F.data.startswith("captcha:"))
async def on_captcha_answer(callback: CallbackQuery, bot: Bot) -> None:
    _, target_id_raw, answer = callback.data.split(":")
    target_id = int(target_id_raw)

    if callback.from_user.id != target_id:
        await callback.answer("این کپچا برای شما نیست.", show_alert=True)
        return

    pending = await repo.get_pending_captcha(callback.message.chat.id, target_id)
    if pending is None:
        await callback.answer()
        return

    if answer == pending.answer:
        try:
            await bot.restrict_chat_member(callback.message.chat.id, target_id, FULL_PERMISSIONS)
        except TelegramBadRequest:
            pass
        await repo.delete_pending_captcha(callback.message.chat.id, target_id)
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.answer("✅ تایید شدید!")
    else:
        await callback.answer("❌ پاسخ اشتباه است.", show_alert=True)
