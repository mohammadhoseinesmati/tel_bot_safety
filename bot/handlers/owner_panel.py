from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.database import repository as repo
from bot.filters.is_owner import IsOwner
from bot.keyboards.inline import (
    back_to_panel_keyboard,
    owner_blocked_keyboard,
    owner_broadcast_confirm_keyboard,
    owner_channels_keyboard,
    owner_groups_keyboard,
    owner_panel_main,
)

router = Router(name="owner_panel")
router.message.filter(F.chat.type == "private", IsOwner())


class PanelStates(StatesGroup):
    waiting_block_id = State()
    waiting_channel = State()
    waiting_broadcast_content = State()


@router.message(Command("panel"))
async def cmd_panel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🛠 <b>پنل مدیریت ربات</b>\n\nیکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=owner_panel_main(),
    )


@router.message(Command("block"))
async def cmd_block(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("استفاده: <code>/block USER_ID</code>")
        return
    try:
        target_id = int(command.args.strip().split()[0])
    except ValueError:
        await message.answer("شناسه کاربری نامعتبر است.")
        return
    await repo.block_installer(target_id, message.from_user.id)
    await message.answer(f"🚫 کاربر <code>{target_id}</code> دیگر نمی‌تواند ربات را به گروهی اضافه کند.")


@router.message(Command("unblock"))
async def cmd_unblock(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("استفاده: <code>/unblock USER_ID</code>")
        return
    try:
        target_id = int(command.args.strip().split()[0])
    except ValueError:
        await message.answer("شناسه کاربری نامعتبر است.")
        return
    removed = await repo.unblock_installer(target_id)
    await message.answer("✅ رفع مسدودیت شد." if removed else "این کاربر مسدود نبود.")


@router.message(Command("blocked"))
async def cmd_blocked(message: Message) -> None:
    items = await repo.list_blocked_installers()
    if not items:
        await message.answer("هیچ کاربری مسدود نشده است.")
        return
    lines = [f"• <code>{item.user_id}</code>" for item in items]
    await message.answer("🚫 کاربران مسدودشده از افزودن ربات:\n" + "\n".join(lines))


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


@router.message(Command("groups"))
async def cmd_groups(message: Message) -> None:
    groups = await repo.list_active_groups()
    if not groups:
        await message.answer("ربات در حال حاضر در هیچ گروهی فعال نیست.")
        return
    lines = [f"• {g.title or g.id} (<code>{g.id}</code>)" for g in groups]
    await message.answer("📋 گروه‌هایی که ربات در آن‌ها فعال است:\n" + "\n".join(lines))


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject, bot: Bot) -> None:
    if not message.reply_to_message and not command.args:
        await message.answer(
            "استفاده تبلیغ/پیام همگانی:\n"
            "• روی یک پیام (متن، عکس، ویدیو و ...) ریپلای کرده و دستور /broadcast را ارسال کنید.\n"
            "• یا مستقیم: <code>/broadcast متن تبلیغ</code>"
        )
        return

    groups = await repo.list_active_groups()
    if not groups:
        await message.answer("هیچ گروه فعالی برای ارسال تبلیغ وجود ندارد.")
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
    groups = await repo.list_active_groups()
    blocked = await repo.list_blocked_installers()
    await message.answer(
        "📊 <b>آمار ربات</b>\n\n"
        f"گروه‌های فعال: {len(groups)}\n"
        f"کاربران مسدودشده: {len(blocked)}"
    )


# ---------- پنل شیشه‌ای مدیریت ----------

PANEL_TITLE = "🛠 <b>پنل مدیریت ربات</b>\n\nیکی از گزینه‌های زیر را انتخاب کنید:"


@router.callback_query(F.data == "panel:main")
async def panel_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(PANEL_TITLE, reply_markup=owner_panel_main())
    await callback.answer()


@router.callback_query(F.data == "panel:close")
async def panel_close(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "panel:groups")
async def panel_groups(callback: CallbackQuery) -> None:
    groups = await repo.list_active_groups()
    text = "📋 <b>گروه‌هایی که ربات در آن‌ها فعال است</b>\n\n"
    text += "برای خارج کردن ربات از یک گروه، روی آن بزنید." if groups else "ربات در حال حاضر در هیچ گروهی فعال نیست."
    await callback.message.edit_text(text, reply_markup=owner_groups_keyboard(groups))
    await callback.answer()


@router.callback_query(F.data.startswith("panel:grp_leave:"))
async def panel_group_leave(callback: CallbackQuery, bot: Bot) -> None:
    chat_id = int(callback.data.split(":")[2])
    try:
        await bot.leave_chat(chat_id)
    except Exception:
        pass
    await repo.set_group_active(chat_id, False)

    groups = await repo.list_active_groups()
    text = "📋 <b>گروه‌هایی که ربات در آن‌ها فعال است</b>\n\n"
    text += "برای خارج کردن ربات از یک گروه، روی آن بزنید." if groups else "ربات در حال حاضر در هیچ گروهی فعال نیست."
    await callback.message.edit_text(text, reply_markup=owner_groups_keyboard(groups))
    await callback.answer("✅ ربات از گروه خارج شد.")


@router.callback_query(F.data == "panel:blocked")
async def panel_blocked(callback: CallbackQuery) -> None:
    items = await repo.list_blocked_installers()
    text = "🚫 <b>کاربران مسدودشده از افزودن ربات به گروه</b>\n\n"
    text += (
        "این کاربران نمی‌توانند ربات را به گروه خود اضافه کنند؛ اگر تلاش کنند ربات خودکار خارج می‌شود.\n\n"
        "برای رفع مسدودیت روی کاربر بزنید."
        if items
        else "هیچ کاربری مسدود نشده است. به‌طور پیش‌فرض همه می‌توانند ربات را به گروه خود اضافه کنند."
    )
    await callback.message.edit_text(text, reply_markup=owner_blocked_keyboard(items))
    await callback.answer()


@router.callback_query(F.data == "panel:bl_add")
async def panel_block_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PanelStates.waiting_block_id)
    await callback.message.edit_text(
        "🆔 شناسه عددی کاربری که می‌خواهید مسدود کنید را ارسال کنید.\n\n"
        "برای گرفتن شناسه عددی، از خود کاربر بخواهید به @userinfobot پیام بدهد و عدد id را برایتان بفرستد.",
        reply_markup=back_to_panel_keyboard(),
    )
    await callback.answer()


@router.message(PanelStates.waiting_block_id)
async def panel_block_receive(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not message.text or not message.text.strip().isdigit():
        await message.answer("❌ شناسه نامعتبر است. فقط عدد ارسال کنید.", reply_markup=back_to_panel_keyboard())
        return
    target_id = int(message.text.strip())
    await repo.block_installer(target_id, message.from_user.id)
    items = await repo.list_blocked_installers()
    await message.answer(
        f"🚫 کاربر <code>{target_id}</code> مسدود شد و دیگر نمی‌تواند ربات را به گروهی اضافه کند.",
        reply_markup=owner_blocked_keyboard(items),
    )


@router.callback_query(F.data.startswith("panel:bl_del:"))
async def panel_block_delete(callback: CallbackQuery) -> None:
    target_id = int(callback.data.split(":")[2])
    await repo.unblock_installer(target_id)
    items = await repo.list_blocked_installers()
    text = "🚫 <b>کاربران مسدودشده از افزودن ربات به گروه</b>\n\n"
    text += "برای رفع مسدودیت روی کاربر بزنید." if items else "هیچ کاربری مسدود نشده است."
    await callback.message.edit_text(text, reply_markup=owner_blocked_keyboard(items))
    await callback.answer("✅ رفع مسدودیت شد.")


@router.callback_query(F.data == "panel:channels")
async def panel_channels(callback: CallbackQuery) -> None:
    channels = await repo.list_force_sub_channels()
    text = "📢 <b>کانال‌های عضویت اجباری</b>\n\n"
    text += "برای حذف روی کانال بزنید." if channels else "کانالی تنظیم نشده است. کانال جدید اضافه کنید."
    await callback.message.edit_text(text, reply_markup=owner_channels_keyboard(channels))
    await callback.answer()


@router.callback_query(F.data == "panel:ch_add")
async def panel_channel_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PanelStates.waiting_channel)
    await callback.message.edit_text(
        "📢 یوزرنیم کانال (مثل @mychannel) یا شناسه عددی آن را ارسال کنید.\n\n"
        "⚠️ ربات باید از قبل عضو یا ادمین آن کانال باشد.",
        reply_markup=back_to_panel_keyboard(),
    )
    await callback.answer()


@router.message(PanelStates.waiting_channel)
async def panel_channel_receive(message: Message, bot: Bot, state: FSMContext) -> None:
    await state.clear()
    if not message.text:
        await message.answer("❌ ورودی نامعتبر است.", reply_markup=back_to_panel_keyboard())
        return
    chat_id = message.text.strip().split()[0]
    title = chat_id
    try:
        chat = await bot.get_chat(chat_id)
        title = chat.title or chat_id
    except Exception:
        pass
    await repo.add_force_sub_channel(chat_id, title, None)
    channels = await repo.list_force_sub_channels()
    await message.answer(f"✅ کانال «{title}» اضافه شد.", reply_markup=owner_channels_keyboard(channels))


@router.callback_query(F.data.startswith("panel:ch_del:"))
async def panel_channel_delete(callback: CallbackQuery) -> None:
    channel_id = int(callback.data.split(":")[2])
    await repo.remove_force_sub_channel_by_id(channel_id)
    channels = await repo.list_force_sub_channels()
    text = "📢 <b>کانال‌های عضویت اجباری</b>\n\n"
    text += "برای حذف روی کانال بزنید." if channels else "کانالی تنظیم نشده است. کانال جدید اضافه کنید."
    await callback.message.edit_text(text, reply_markup=owner_channels_keyboard(channels))
    await callback.answer("✅ حذف شد.")


@router.callback_query(F.data == "panel:stats")
async def panel_stats(callback: CallbackQuery) -> None:
    groups = await repo.list_active_groups()
    blocked = await repo.list_blocked_installers()
    channels = await repo.list_force_sub_channels()
    await callback.message.edit_text(
        "📊 <b>آمار ربات</b>\n\n"
        f"گروه‌های فعال: {len(groups)}\n"
        f"کاربران مسدودشده: {len(blocked)}\n"
        f"کانال‌های عضویت اجباری: {len(channels)}",
        reply_markup=back_to_panel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "panel:broadcast")
async def panel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    groups = await repo.list_active_groups()
    if not groups:
        await callback.answer("هیچ گروه فعالی برای ارسال وجود ندارد.", show_alert=True)
        return
    await state.set_state(PanelStates.waiting_broadcast_content)
    await callback.message.edit_text(
        "📣 پیام تبلیغاتی خود را ارسال کنید (متن، عکس، ویدیو و ...).\n"
        f"این پیام پس از تایید شما به {len(groups)} گروه فعال ارسال خواهد شد.",
        reply_markup=back_to_panel_keyboard(),
    )
    await callback.answer()


@router.message(PanelStates.waiting_broadcast_content)
async def panel_broadcast_receive(message: Message, state: FSMContext) -> None:
    groups = await repo.list_active_groups()
    if not groups:
        await state.clear()
        await message.answer("هیچ گروه فعالی برای ارسال وجود ندارد.", reply_markup=back_to_panel_keyboard())
        return

    await state.update_data(source_chat_id=message.chat.id, source_message_id=message.message_id)
    await message.answer(
        "این پیام آماده ارسال است. آیا مطمئن هستید؟",
        reply_markup=owner_broadcast_confirm_keyboard(len(groups)),
    )


@router.callback_query(F.data == "panel:bc_cancel")
async def panel_broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ ارسال لغو شد.", reply_markup=owner_panel_main())
    await callback.answer()


@router.callback_query(F.data == "panel:bc_confirm")
async def panel_broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()
    source_chat_id = data.get("source_chat_id")
    source_message_id = data.get("source_message_id")
    if not source_chat_id or not source_message_id:
        await callback.answer("خطا: پیامی برای ارسال یافت نشد.", show_alert=True)
        return

    groups = await repo.list_active_groups()
    await callback.message.edit_text(f"⏳ در حال ارسال به {len(groups)} گروه...")
    await callback.answer()

    sent, failed = 0, 0
    for group in groups:
        try:
            await bot.copy_message(group.id, source_chat_id, source_message_id)
            sent += 1
        except Exception:
            failed += 1

    await callback.message.edit_text(
        f"✅ ارسال شد به {sent} گروه.\n❌ ناموفق: {failed} گروه.",
        reply_markup=owner_panel_main(),
    )
