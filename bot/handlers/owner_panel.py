from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.database import repository as repo
from bot.filters.is_owner import IsOwner

router = Router(name="owner_panel")
router.message.filter(F.chat.type == "private", IsOwner())


@router.message(Command("approve"))
async def cmd_approve(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("استفاده: <code>/approve USER_ID</code>")
        return
    try:
        target_id = int(command.args.strip().split()[0])
    except ValueError:
        await message.answer("شناسه کاربری نامعتبر است.")
        return
    await repo.add_to_whitelist(target_id, message.from_user.id)
    await message.answer(
        f"✅ کاربر <code>{target_id}</code> اکنون مجاز است ربات را به گروه خود اضافه کند."
    )


@router.message(Command("unapprove"))
async def cmd_unapprove(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("استفاده: <code>/unapprove USER_ID</code>")
        return
    try:
        target_id = int(command.args.strip().split()[0])
    except ValueError:
        await message.answer("شناسه کاربری نامعتبر است.")
        return
    removed = await repo.remove_from_whitelist(target_id)
    await message.answer("✅ حذف شد." if removed else "این کاربر در لیست مجاز نبود.")


@router.message(Command("whitelist"))
async def cmd_whitelist(message: Message) -> None:
    items = await repo.list_whitelist()
    if not items:
        await message.answer("لیست کاربران مجاز خالی است.")
        return
    lines = [f"• <code>{item.user_id}</code>" for item in items]
    await message.answer("👥 کاربران مجاز به افزودن ربات به گروه:\n" + "\n".join(lines))


@router.message(Command("addchannel"))
async def cmd_addchannel(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("استفاده: <code>/addchannel @channel_username</code> یا شناسه عددی کانال")
        return
    chat_id = command.args.strip().split()[0]
    title = chat_id
    try:
        chat = await message.bot.get_chat(chat_id)
        title = chat.title or chat_id
    except Exception:
        pass
    await repo.add_force_sub_channel(chat_id, title, None)
    await message.answer(f"✅ کانال «{title}» به لیست عضویت اجباری اضافه شد.")


@router.message(Command("delchannel"))
async def cmd_delchannel(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("استفاده: <code>/delchannel @channel_username</code>")
        return
    chat_id = command.args.strip().split()[0]
    removed = await repo.remove_force_sub_channel(chat_id)
    await message.answer("✅ حذف شد." if removed else "این کانال در لیست نبود.")


@router.message(Command("channels"))
async def cmd_channels(message: Message) -> None:
    channels = await repo.list_force_sub_channels()
    if not channels:
        await message.answer("کانالی برای عضویت اجباری تنظیم نشده است.")
        return
    lines = [f"• {c.title or c.chat_id} ({c.chat_id})" for c in channels]
    await message.answer("📢 کانال‌های عضویت اجباری:\n" + "\n".join(lines))


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject, bot: Bot) -> None:
    if not message.reply_to_message and not command.args:
        await message.answer(
            "استفاده تبلیغ/پیام همگانی:\n"
            "• روی یک پیام (متن، عکس، ویدیو و ...) ریپلای کرده و دستور /broadcast را ارسال کنید.\n"
            "• یا مستقیم: <code>/broadcast متن تبلیغ</code>"
        )
        return

    groups = await repo.list_approved_groups()
    if not groups:
        await message.answer("هیچ گروه تاییدشده‌ای برای ارسال تبلیغ وجود ندارد.")
        return

    status = await message.answer(f"⏳ در حال ارسال به {len(groups)} گروه...")

    sent, failed = 0, 0
    for group in groups:
        try:
            if message.reply_to_message:
                await bot.copy_message(group.id, message.chat.id, message.reply_to_message.message_id)
            else:
                await bot.send_message(group.id, command.args)
            sent += 1
        except Exception:
            failed += 1

    await status.edit_text(f"✅ ارسال شد به {sent} گروه.\n❌ ناموفق: {failed} گروه.")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    groups = await repo.list_approved_groups()
    whitelist = await repo.list_whitelist()
    await message.answer(
        "📊 <b>آمار ربات</b>\n\n"
        f"گروه‌های فعال: {len(groups)}\n"
        f"کاربران مجاز افزودن به گروه: {len(whitelist)}"
    )
