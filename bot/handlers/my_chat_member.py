from __future__ import annotations

from aiogram import Bot, Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated

from bot.config import config
from bot.database import repository as repo

router = Router(name="my_chat_member")


@router.my_chat_member()
async def on_bot_membership_changed(event: ChatMemberUpdated, bot: Bot) -> None:
    if event.chat.type not in ("group", "supergroup"):
        return

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    was_in = old_status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR)
    is_in = new_status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR)

    if is_in and not was_in:
        await _handle_bot_added(event, bot)
    elif was_in and not is_in:
        await repo.set_group_active(event.chat.id, False)


async def _handle_bot_added(event: ChatMemberUpdated, bot: Bot) -> None:
    adder_id = event.from_user.id
    is_blocked = adder_id not in config.owner_ids and await repo.is_blocked_installer(adder_id)

    if is_blocked:
        try:
            await bot.send_message(
                event.chat.id,
                "⛔️ افزودن این ربات توسط شما مسدود شده است.\n"
                "برای رفع مسدودیت با پشتیبانی مالک ربات در ارتباط باشید.",
            )
        except Exception:
            pass

        for owner_id in config.owner_ids:
            try:
                await bot.send_message(
                    owner_id,
                    "🚫 یک کاربر مسدودشده تلاش کرد ربات را به گروه اضافه کند:\n"
                    f"گروه: {event.chat.title} (<code>{event.chat.id}</code>)\n"
                    f"کاربر: {event.from_user.full_name} (<code>{adder_id}</code>)\n\n"
                    "ربات به‌طور خودکار از گروه خارج شد.",
                )
            except Exception:
                pass

        try:
            await bot.leave_chat(event.chat.id)
        except Exception:
            pass
        return

    await repo.get_or_create_group(event.chat.id, event.chat.title, adder_id)

    try:
        await bot.send_message(
            event.chat.id,
            "✅ ربات محافظ گروه با موفقیت فعال شد!\n"
            "برای مشاهده و تغییر تنظیمات محافظتی از دستور /settings استفاده کنید.",
        )
    except Exception:
        pass

    for owner_id in config.owner_ids:
        try:
            await bot.send_message(
                owner_id,
                "✅ ربات به یک گروه جدید اضافه شد:\n"
                f"گروه: {event.chat.title} (<code>{event.chat.id}</code>)\n"
                f"توسط: {event.from_user.full_name} (<code>{adder_id}</code>)\n\n"
                "در صورت نیاز به حذف ربات از این گروه، از پنل مدیریت (/panel ← گروه‌های ربات) استفاده کنید.",
            )
        except Exception:
            pass
