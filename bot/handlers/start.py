from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from bot.database import repository as repo
from bot.keyboards.inline import start_menu
from bot.utils.permissions import is_owner

router = Router(name="start")

HELP_TEXT = (
    "📜 <b>راهنمای ربات</b>\n\n"
    "🛠 برای مالک ربات: دستور /panel یک پنل مدیریت با دکمه باز می‌کند "
    "(کاربران مجاز، کانال‌های عضویت اجباری، ارسال تبلیغ، آمار).\n\n"
    "دستورات مدیریتی گروه (فقط برای ادمین‌ها):\n"
    "/settings - تنظیمات محافظتی گروه\n"
    "/ban /unban /mute /unmute /kick - مدیریت اعضا (ریپلای روی پیام کاربر)\n"
    "/warn /unwarn /warns - سیستم اخطار\n"
    "/lock /unlock &lt;link|username|forward|photo|video|sticker&gt; - قفل کردن محتوا\n"
    "/rules /setrules - قوانین گروه\n"
    "/setwelcome - تنظیم پیام خوش‌آمدگویی\n"
    "/addword /delword /words - مدیریت کلمات ممنوعه\n"
    "/pin /unpin - پین کردن پیام\n"
    "/promote /demote - مدیریت ادمین‌ها\n"
)


@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: Message, bot: Bot) -> None:
    await repo.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    me = await bot.get_me()
    await message.answer(
        "👋 سلام! به ربات محافظ گروه خوش آمدید.\n\n"
        "با این ربات می‌توانید از گروه خود در برابر اسپم، فلاد، لینک‌های مزاحم، کلمات نامناسب و اعضای مزاحم "
        "محافظت کنید.\n\n"
        "برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=start_menu(me.username, is_owner(message.from_user.id)),
    )


@router.message(Command("help"), F.chat.type == "private")
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.callback_query(F.data == "help:show")
async def help_show(callback: CallbackQuery) -> None:
    await callback.message.answer(HELP_TEXT)
    await callback.answer()


@router.callback_query(F.data == "checksub")
async def check_subscription(callback: CallbackQuery, bot: Bot) -> None:
    channels = await repo.list_force_sub_channels()
    not_joined = []
    for channel in channels:
        try:
            member = await bot.get_chat_member(channel.chat_id, callback.from_user.id)
            if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
                not_joined.append(channel)
        except Exception:
            not_joined.append(channel)

    if not_joined:
        await callback.answer("هنوز در همه کانال‌ها عضو نشده‌اید!", show_alert=True)
        return

    await callback.answer("✅ عضویت شما تایید شد.")
    try:
        await callback.message.delete()
    except Exception:
        pass

    me = await bot.get_me()
    await callback.message.answer(
        "👋 خوش آمدید! از منوی زیر گزینه مورد نظر را انتخاب کنید:",
        reply_markup=start_menu(me.username, is_owner(callback.from_user.id)),
    )
