from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BlockedInstaller(Base):
    """کاربرانی که مالک ربات از افزودن ربات به گروه منع کرده است."""

    __tablename__ = "blocked_installers"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    blocked_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    blocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # chat id
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    added_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # محافظت‌ها
    anti_flood: Mapped[bool] = mapped_column(Boolean, default=True)
    flood_limit: Mapped[int] = mapped_column(Integer, default=6)
    flood_seconds: Mapped[int] = mapped_column(Integer, default=8)
    flood_action: Mapped[str] = mapped_column(String(20), default="mute")  # mute/kick/ban

    bad_words_filter: Mapped[bool] = mapped_column(Boolean, default=True)

    captcha: Mapped[bool] = mapped_column(Boolean, default=True)
    captcha_timeout: Mapped[int] = mapped_column(Integer, default=120)

    welcome_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    welcome_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    warn_limit: Mapped[int] = mapped_column(Integer, default=3)
    warn_action: Mapped[str] = mapped_column(String(20), default="mute")  # mute/kick/ban

    lock_links: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_forward: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_photo: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_video: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_sticker: Mapped[bool] = mapped_column(Boolean, default=False)
    lock_usernames: Mapped[bool] = mapped_column(Boolean, default=False)


class WarnRecord(Base):
    __tablename__ = "warnings"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_warning_group_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(BigInteger)
    count: Mapped[int] = mapped_column(Integer, default=0)


class BadWord(Base):
    __tablename__ = "bad_words"
    __table_args__ = (UniqueConstraint("group_id", "word", name="uq_bad_word_group_word"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger)
    word: Mapped[str] = mapped_column(String(255))


class ForceSubChannel(Base):
    """کانال‌هایی که کاربران باید قبل از استفاده از ربات در آن‌ها عضو باشند."""

    __tablename__ = "force_sub_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(String(64))  # مثل @channel یا -100xxxxxxxxxx
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invite_link: Mapped[str | None] = mapped_column(String(255), nullable=True)


class PendingCaptcha(Base):
    __tablename__ = "pending_captcha"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(BigInteger)
    message_id: Mapped[int] = mapped_column(Integer)
    deadline: Mapped[datetime] = mapped_column(DateTime)
    answer: Mapped[str] = mapped_column(String(8))
