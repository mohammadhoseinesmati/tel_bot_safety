from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config import config
from bot.database.db import init_db
from bot.handlers import group_admin, my_chat_member, owner_panel, protection, start, support, welcome
from bot.middlewares.force_subscribe import ForceSubscribeMiddleware
from bot.utils.captcha_scheduler import start_captcha_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="شروع کار با ربات"),
            BotCommand(command="help", description="راهنمای ربات"),
            BotCommand(command="panel", description="پنل مدیریت ربات (فقط مالک)"),
        ]
    )


async def main() -> None:
    await init_db()

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(ForceSubscribeMiddleware())

    # ترتیب ثبت روتر مهم است: دستورات مالک/ادمین قبل از هندلر عمومی محافظت بررسی شوند.
    dp.include_router(my_chat_member.router)
    dp.include_router(owner_panel.router)
    dp.include_router(group_admin.router)
    dp.include_router(welcome.router)
    dp.include_router(protection.router)
    dp.include_router(support.router)
    dp.include_router(start.router)

    await _set_commands(bot)
    start_captcha_scheduler(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("ربات در حال اجرا است...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
