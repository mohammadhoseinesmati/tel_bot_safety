from __future__ import annotations

from typing import Sequence

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.models import ForceSubChannel, Group, Whitelist


def start_menu(bot_username: str, is_owner: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ افزودن ربات به گروه", url=f"https://t.me/{bot_username}?startgroup=true")
    builder.button(text="📞 پشتیبانی", callback_data="support:start")
    builder.button(text="📜 راهنما", callback_data="help:show")
    if is_owner:
        builder.button(text="🛠 پنل مدیریت ربات", callback_data="panel:main")
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


def owner_panel_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 کاربران مجاز به افزودن ربات", callback_data="panel:whitelist")
    builder.button(text="📢 کانال‌های عضویت اجباری", callback_data="panel:channels")
    builder.button(text="📣 ارسال تبلیغ به گروه‌ها", callback_data="panel:broadcast")
    builder.button(text="📊 آمار ربات", callback_data="panel:stats")
    builder.button(text="✖️ بستن", callback_data="panel:close")
    builder.adjust(1)
    return builder.as_markup()


def owner_whitelist_keyboard(items: Sequence[Whitelist]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(text=f"❌ حذف {item.user_id}", callback_data=f"panel:wl_del:{item.user_id}")
    builder.button(text="➕ افزودن کاربر جدید", callback_data="panel:wl_add")
    builder.button(text="🔙 بازگشت", callback_data="panel:main")
    builder.adjust(1)
    return builder.as_markup()


def owner_channels_keyboard(channels: Sequence[ForceSubChannel]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for channel in channels:
        label = channel.title or channel.chat_id
        builder.button(text=f"❌ حذف {label}", callback_data=f"panel:ch_del:{channel.id}")
    builder.button(text="➕ افزودن کانال", callback_data="panel:ch_add")
    builder.button(text="🔙 بازگشت", callback_data="panel:main")
    builder.adjust(1)
    return builder.as_markup()


def owner_broadcast_confirm_keyboard(count: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"✅ ارسال به {count} گروه", callback_data="panel:bc_confirm")
    builder.button(text="❌ لغو", callback_data="panel:bc_cancel")
    builder.adjust(1)
    return builder.as_markup()


def back_to_panel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 بازگشت", callback_data="panel:main")
    builder.adjust(1)
    return builder.as_markup()
