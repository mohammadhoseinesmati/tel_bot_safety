from __future__ import annotations

from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from bot.database import repository as repo
from bot.filters.is_admin import IsGroupAdmin
from bot.keyboards.inline import group_settings_keyboard
from bot.utils.permissions import FULL_PERMISSIONS, RESTRICTED_PERMISSIONS, is_group_admin

router = Router(name="group_admin")
router.message.filter(F.chat.type.in_({"group", "supergroup"}), IsGroupAdmin())

LOCK_TYPES = {
    "link": "lock_links",
    "username": "lock_usernames",
    "forward": "lock_forward",
    "photo": "lock_photo",
    "video": "lock_video",
    "sticker": "lock_sticker",
}


def _resolve_target_and_reason(message: Message, command: CommandObject) -> tuple[int, str, str] | None:
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        reason = command.args.strip() if command.args else "نامشخص"
        return user.id, user.full_name, reason
    if command.args:
        parts = command.args.strip().split(maxsplit=1)
        if parts[0].lstrip("-").isdigit():
            reason = parts[1] if len(parts) > 1 else "نامشخص"
            return int(parts[0]), parts[0], reason
    return None


@router.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject, bot: Bot) -> None:
    target = _resolve_target_and_reason(message, command)
    if not target:
        await message.answer("کاربر مورد نظر را ریپلای کنید یا شناسه عددی وارد کنید.\nاستفاده: /ban [دلیل]")
        return
    user_id, name, reason = target
    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.answer(f"⛔️ کاربر {name} از گروه بن شد.\nدلیل: {reason}")
    except TelegramBadRequest as e:
        await message.answer(f"❌ خطا: {e.message}")


@router.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject, bot: Bot) -> None:
    target = _resolve_target_and_reason(message, command)
    if not target:
        await message.answer("شناسه عددی کاربر را وارد کنید.\nاستفاده: /unban USER_ID")
        return
    user_id, name, _ = target
    try:
        await bot.unban_chat_member(message.chat.id, user_id, only_if_banned=True)
        await message.answer(f"✅ کاربر {name} آنبن شد.")
    except TelegramBadRequest as e:
        await message.answer(f"❌ خطا: {e.message}")


@router.message(Command("kick"))
async def cmd_kick(message: Message, command: CommandObject, bot: Bot) -> None:
    target = _resolve_target_and_reason(message, command)
    if not target:
        await message.answer("کاربر مورد نظر را ریپلای کنید.\nاستفاده: /kick [دلیل]")
        return
    user_id, name, reason = target
    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await bot.unban_chat_member(message.chat.id, user_id)
        await message.answer(f"👢 کاربر {name} از گروه اخراج شد.\nدلیل: {reason}")
    except TelegramBadRequest as e:
        await message.answer(f"❌ خطا: {e.message}")


@router.message(Command("mute"))
async def cmd_mute(message: Message, command: CommandObject, bot: Bot) -> None:
    target = _resolve_target_and_reason(message, command)
    if not target:
        await message.answer("کاربر مورد نظر را ریپلای کنید.\nاستفاده: /mute [مدت به دقیقه] [دلیل]")
        return
    user_id, name, reason = target

    minutes = None
    until = None
    reason_parts = reason.split(maxsplit=1)
    if reason_parts and reason_parts[0].isdigit():
        minutes = int(reason_parts[0])
        reason = reason_parts[1] if len(reason_parts) > 1 else "نامشخص"
        until = datetime.utcnow() + timedelta(minutes=minutes)

    try:
        await bot.restrict_chat_member(message.chat.id, user_id, RESTRICTED_PERMISSIONS, until_date=until)
        duration_text = f"به مدت {minutes} دقیقه" if minutes else "به صورت دائم"
        await message.answer(f"🔇 کاربر {name} سایلنت شد {duration_text}.\nدلیل: {reason}")
    except TelegramBadRequest as e:
        await message.answer(f"❌ خطا: {e.message}")


@router.message(Command("unmute"))
async def cmd_unmute(message: Message, command: CommandObject, bot: Bot) -> None:
    target = _resolve_target_and_reason(message, command)
    if not target:
        await message.answer("کاربر مورد نظر را ریپلای کنید.")
        return
    user_id, name, _ = target
    try:
        await bot.restrict_chat_member(message.chat.id, user_id, FULL_PERMISSIONS)
        await message.answer(f"🔊 سکوت کاربر {name} برداشته شد.")
    except TelegramBadRequest as e:
        await message.answer(f"❌ خطا: {e.message}")


@router.message(Command("warn"))
async def cmd_warn(message: Message, command: CommandObject, bot: Bot) -> None:
    target = _resolve_target_and_reason(message, command)
    if not target:
        await message.answer("کاربر مورد نظر را ریپلای کنید.\nاستفاده: /warn [دلیل]")
        return
    user_id, name, reason = target

    group = await repo.get_or_create_group(message.chat.id, message.chat.title, message.from_user.id)
    count = await repo.add_warning(message.chat.id, user_id)

    if count >= group.warn_limit:
        await repo.reset_warning(message.chat.id, user_id)
        try:
            if group.warn_action == "ban":
                await bot.ban_chat_member(message.chat.id, user_id)
                result_text = "بن شد"
            elif group.warn_action == "kick":
                await bot.ban_chat_member(message.chat.id, user_id)
                await bot.unban_chat_member(message.chat.id, user_id)
                result_text = "اخراج شد"
            else:
                await bot.restrict_chat_member(
                    message.chat.id, user_id, RESTRICTED_PERMISSIONS,
                    until_date=datetime.utcnow() + timedelta(hours=1),
                )
                result_text = "به مدت ۱ ساعت سایلنت شد"
            await message.answer(f"⚠️ کاربر {name} به سقف اخطار ({group.warn_limit}) رسید و {result_text}.")
        except TelegramBadRequest as e:
            await message.answer(f"❌ خطا در اعمال مجازات: {e.message}")
    else:
        await message.answer(f"⚠️ کاربر {name} اخطار گرفت. ({count}/{group.warn_limit})\nدلیل: {reason}")


@router.message(Command("unwarn"))
async def cmd_unwarn(message: Message, command: CommandObject) -> None:
    target = _resolve_target_and_reason(message, command)
    if not target:
        await message.answer("کاربر مورد نظر را ریپلای کنید.")
        return
    user_id, name, _ = target
    await repo.reset_warning(message.chat.id, user_id)
    await message.answer(f"✅ اخطارهای کاربر {name} پاک شد.")


@router.message(Command("warns"))
async def cmd_warns(message: Message, command: CommandObject) -> None:
    target = _resolve_target_and_reason(message, command)
    if not target:
        await message.answer("کاربر مورد نظر را ریپلای کنید.")
        return
    user_id, name, _ = target
    group = await repo.get_or_create_group(message.chat.id, message.chat.title, message.from_user.id)
    count = await repo.get_warning_count(message.chat.id, user_id)
    await message.answer(f"⚠️ کاربر {name}: {count}/{group.warn_limit} اخطار")


@router.message(Command("pin"))
async def cmd_pin(message: Message, bot: Bot) -> None:
    if not message.reply_to_message:
        await message.answer("روی پیامی که می‌خواهید پین شود ریپلای کنید.")
        return
    try:
        await bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        await message.answer("📌 پیام پین شد.")
    except TelegramBadRequest as e:
        await message.answer(f"❌ خطا: {e.message}")


@router.message(Command("unpin"))
async def cmd_unpin(message: Message, bot: Bot) -> None:
    try:
        await bot.unpin_all_chat_messages(message.chat.id)
        await message.answer("📌 همه پیام‌ها آنپین شدند.")
    except TelegramBadRequest as e:
        await message.answer(f"❌ خطا: {e.message}")


@router.message(Command("promote"))
async def cmd_promote(message: Message, command: CommandObject, bot: Bot) -> None:
    target = _resolve_target_and_reason(message, command)
    if not target:
        await message.answer("کاربر مورد نظر را ریپلای کنید.")
        return
    user_id, name, _ = target
    try:
        await bot.promote_chat_member(
            message.chat.id, user_id,
            can_delete_messages=True, can_restrict_members=True,
            can_pin_messages=True, can_invite_users=True,
        )
        await message.answer(f"🌟 کاربر {name} ادمین شد.")
    except TelegramBadRequest as e:
        await message.answer(f"❌ خطا: {e.message}")


@router.message(Command("demote"))
async def cmd_demote(message: Message, command: CommandObject, bot: Bot) -> None:
    target = _resolve_target_and_reason(message, command)
    if not target:
        await message.answer("کاربر مورد نظر را ریپلای کنید.")
        return
    user_id, name, _ = target
    try:
        await bot.promote_chat_member(
            message.chat.id, user_id,
            can_delete_messages=False, can_restrict_members=False,
            can_pin_messages=False, can_invite_users=False,
        )
        await message.answer(f"⬇️ ادمین بودن کاربر {name} لغو شد.")
    except TelegramBadRequest as e:
        await message.answer(f"❌ خطا: {e.message}")


@router.message(Command("rules"))
async def cmd_rules(message: Message) -> None:
    group = await repo.get_group(message.chat.id)
    text = group.rules_text if group and group.rules_text else "قانونی برای این گروه تنظیم نشده است."
    await message.answer(f"📜 <b>قوانین گروه</b>\n\n{text}")


@router.message(Command("setrules"))
async def cmd_setrules(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("استفاده: <code>/setrules متن قوانین</code>")
        return
    await repo.get_or_create_group(message.chat.id, message.chat.title, message.from_user.id)
    await repo.update_group_settings(message.chat.id, rules_text=command.args)
    await message.answer("✅ قوانین گروه ذخیره شد.")


@router.message(Command("setwelcome"))
async def cmd_setwelcome(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer(
            "استفاده: <code>/setwelcome متن خوش‌آمدگویی</code>\n"
            "می‌توانید از {name} برای نام کاربر جدید استفاده کنید."
        )
        return
    await repo.get_or_create_group(message.chat.id, message.chat.title, message.from_user.id)
    await repo.update_group_settings(message.chat.id, welcome_text=command.args)
    await message.answer("✅ پیام خوش‌آمدگویی ذخیره شد.")


@router.message(Command("addword"))
async def cmd_addword(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("استفاده: <code>/addword کلمه</code>")
        return
    added = await repo.add_bad_word(message.chat.id, command.args)
    await message.answer("✅ اضافه شد." if added else "این کلمه قبلا اضافه شده است.")


@router.message(Command("delword"))
async def cmd_delword(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("استفاده: <code>/delword کلمه</code>")
        return
    removed = await repo.remove_bad_word(message.chat.id, command.args)
    await message.answer("✅ حذف شد." if removed else "این کلمه در لیست نبود.")


@router.message(Command("words"))
async def cmd_words(message: Message) -> None:
    words = await repo.list_bad_words(message.chat.id)
    if not words:
        await message.answer("لیست کلمات ممنوعه خالی است.")
        return
    await message.answer("🚫 کلمات ممنوعه:\n" + "\n".join(f"• {w}" for w in words))


async def _handle_lock(message: Message, command: CommandObject, lock: bool) -> None:
    key = command.args.strip() if command.args else ""
    if key not in LOCK_TYPES:
        await message.answer(
            "انواع قابل قفل: " + ", ".join(LOCK_TYPES.keys()) + "\n"
            f"استفاده: /{'lock' if lock else 'unlock'} <نوع>"
        )
        return
    field_name = LOCK_TYPES[key]
    await repo.get_or_create_group(message.chat.id, message.chat.title, message.from_user.id)
    await repo.update_group_settings(message.chat.id, **{field_name: lock})
    await message.answer(f"✅ {key} {'قفل شد' if lock else 'باز شد'}.")


@router.message(Command("lock"))
async def cmd_lock(message: Message, command: CommandObject) -> None:
    await _handle_lock(message, command, lock=True)


@router.message(Command("unlock"))
async def cmd_unlock(message: Message, command: CommandObject) -> None:
    await _handle_lock(message, command, lock=False)


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    group = await repo.get_or_create_group(message.chat.id, message.chat.title, message.from_user.id)
    await message.answer("⚙️ تنظیمات محافظتی گروه:", reply_markup=group_settings_keyboard(group))


@router.callback_query(F.data.startswith("gs:"))
async def settings_toggle(callback: CallbackQuery, bot: Bot) -> None:
    if not await is_group_admin(bot, callback.message.chat.id, callback.from_user.id):
        await callback.answer("فقط ادمین‌های گروه می‌توانند تنظیمات را تغییر دهند.", show_alert=True)
        return

    action = callback.data.split(":", 1)[1]
    if action == "close":
        await callback.message.delete()
        await callback.answer()
        return

    group = await repo.toggle_group_setting(callback.message.chat.id, action)
    if group is None:
        await callback.answer("خطا در بروزرسانی تنظیمات.", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=group_settings_keyboard(group))
    await callback.answer("✅ بروزرسانی شد.")
