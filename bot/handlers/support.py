from __future__ import annotations

import re

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.config import config

router = Router(name="support")

USER_ID_PATTERN = re.compile(r"🆔 کاربر: <code>(\d+)</code>")


class SupportStates(StatesGroup):
    waiting_message = State()


@router.callback_query(F.data == "support:start")
async def support_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SupportStates.waiting_message)
    await callback.message.answer("✍️ پیام خود را برای پشتیبانی ارسال کنید:")
    await callback.answer()


@router.message(SupportStates.waiting_message, F.chat.type == "private")
async def support_forward(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.clear()

    if not config.owner_ids:
        await message.answer("در حال حاضر پشتیبانی در دسترس نیست.")
        return

    user = message.from_user
    targets = [config.support_chat_id] if config.support_chat_id else list(config.owner_ids)

    for target_id in targets:
        try:
            header = await bot.send_message(
                target_id,
                "📩 پیام پشتیبانی جدید\n"
                f"🆔 کاربر: <code>{user.id}</code>\n"
                f"👤 نام: {user.full_name}\n"
                f"یوزرنیم: @{user.username if user.username else '-'}\n\n"
                "برای پاسخ، روی پیام بعدی ریپلای کنید.",
            )
            await message.copy_to(chat_id=target_id, reply_to_message_id=header.message_id)
        except Exception:
            pass

    await message.answer("✅ پیام شما برای پشتیبانی ارسال شد. به زودی پاسخ داده می‌شود.")


@router.message(F.chat.type == "private", F.from_user.id.in_(config.owner_ids), F.reply_to_message)
async def support_reply(message: Message) -> None:
    replied = message.reply_to_message
    candidates = [replied.text or replied.caption or ""]
    if replied.reply_to_message:
        candidates.append(replied.reply_to_message.text or replied.reply_to_message.caption or "")

    match = None
    for candidate in candidates:
        match = USER_ID_PATTERN.search(candidate)
        if match:
            break

    if not match:
        return

    target_id = int(match.group(1))
    try:
        await message.copy_to(chat_id=target_id)
        await message.answer("✅ پاسخ شما ارسال شد.")
    except Exception:
        await message.answer("❌ ارسال پاسخ ناموفق بود (احتمالا کاربر ربات را مسدود کرده است).")
