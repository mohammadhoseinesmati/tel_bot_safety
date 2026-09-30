from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _parse_ids(raw: str) -> set[int]:
    return {int(x) for x in raw.replace(" ", "").split(",") if x}


def _parse_optional_id(raw: str | None) -> int | None:
    return int(raw) if raw else None


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    owner_ids: set[int] = field(default_factory=lambda: _parse_ids(os.getenv("OWNER_IDS", "")))
    support_chat_id: int | None = field(default_factory=lambda: _parse_optional_id(os.getenv("SUPPORT_CHAT_ID")))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db"))


config = Config()

if not config.bot_token:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است. آن را در فایل .env قرار دهید.")
if not config.owner_ids:
    raise RuntimeError("OWNER_IDS تنظیم نشده است. حداقل یک شناسه عددی مالک را در فایل .env قرار دهید.")
