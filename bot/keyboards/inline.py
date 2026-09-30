from __future__ import annotations

from typing import Sequence

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.models import ForceSubChannel, Group


def start_menu(bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ افزودن ربات به گروه", url=f"https://t.me/{bot_username}?startgroup=true")
    builder.button(text="📞 پشتیبانی", callback_data="support:start")
    builder.button(text="📜 راهنما", callback_data="help:show")
    builder.adjust(1)
    return builder.as_markup()


def join_channels_keyboard(channels: Sequence[ForceSubChannel]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for channel in channels:
        link = channel.invite_link or f"https://t.me/{channel.chat_id.lstrip('@')}"
        builder.button(text=f"📢 عضویت در {channel.title or channel.chat_id}", url=link)
    builder.button(text="✅ عضو شدم", callback_data="checksub")
    builder.adjust(1)
    return builder.as_markup()


def group_settings_keyboard(group: Group) -> InlineKeyboardMarkup:
    def onoff(value: bool) -> str:
        return "🟢 فعال" if value else "🔴 غیرفعال"

    builder = InlineKeyboardBuilder()
    builder.button(text=f"ضد فلاد: {onoff(group.anti_flood)}", callback_data="gs:anti_flood")
    builder.button(text=f"فیلتر کلمات بد: {onoff(group.bad_words_filter)}", callback_data="gs:bad_words_filter")
    builder.button(text=f"کپچای اعضای جدید: {onoff(group.captcha)}", callback_data="gs:captcha")
    builder.button(text=f"پیام خوش‌آمد: {onoff(group.welcome_enabled)}", callback_data="gs:welcome_enabled")
    builder.button(text=f"قفل لینک: {onoff(group.lock_links)}", callback_data="gs:lock_links")
    builder.button(text=f"قفل یوزرنیم: {onoff(group.lock_usernames)}", callback_data="gs:lock_usernames")
    builder.button(text=f"قفل فوروارد: {onoff(group.lock_forward)}", callback_data="gs:lock_forward")
    builder.button(text=f"قفل عکس: {onoff(group.lock_photo)}", callback_data="gs:lock_photo")
    builder.button(text=f"قفل ویدیو: {onoff(group.lock_video)}", callback_data="gs:lock_video")
    builder.button(text=f"قفل استیکر: {onoff(group.lock_sticker)}", callback_data="gs:lock_sticker")
    builder.button(text="✖️ بستن", callback_data="gs:close")
    builder.adjust(1)
    return builder.as_markup()
