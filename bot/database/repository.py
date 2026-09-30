from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from bot.database.db import async_session
from bot.database.models import BadWord, BlockedInstaller, ForceSubChannel, Group, PendingCaptcha, User, WarnRecord


# ---------- Users ----------

async def get_or_create_user(user_id: int, username: str | None, first_name: str | None) -> User:
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user is None:
            user = User(id=user_id, username=username, first_name=first_name)
            session.add(user)
            await session.commit()
        return user


# ---------- Blocked installers (کاربران منع‌شده از افزودن ربات به گروه) ----------
# پیش‌فرض: هر کسی می‌تواند ربات را به گروه خود اضافه کند، مگر این‌که در این لیست مسدود شده باشد.

async def is_blocked_installer(user_id: int) -> bool:
    async with async_session() as session:
        return await session.get(BlockedInstaller, user_id) is not None


async def block_installer(user_id: int, blocked_by: int, note: str | None = None) -> None:
    async with async_session() as session:
        existing = await session.get(BlockedInstaller, user_id)
        if existing is None:
            session.add(BlockedInstaller(user_id=user_id, blocked_by=blocked_by, note=note))
            await session.commit()


async def unblock_installer(user_id: int) -> bool:
    async with async_session() as session:
        existing = await session.get(BlockedInstaller, user_id)
        if existing is None:
            return False
        await session.delete(existing)
        await session.commit()
        return True


async def list_blocked_installers() -> list[BlockedInstaller]:
    async with async_session() as session:
        result = await session.execute(select(BlockedInstaller))
        return list(result.scalars().all())


# ---------- Groups ----------

async def get_group(group_id: int) -> Group | None:
    async with async_session() as session:
        return await session.get(Group, group_id)


async def get_or_create_group(group_id: int, title: str | None, added_by: int | None) -> Group:
    async with async_session() as session:
        group = await session.get(Group, group_id)
        if group is None:
            group = Group(id=group_id, title=title, added_by=added_by)
            session.add(group)
        else:
            group.title = title or group.title
            group.is_active = True
        await session.commit()
        await session.refresh(group)
        return group


async def set_group_active(group_id: int, active: bool) -> None:
    async with async_session() as session:
        group = await session.get(Group, group_id)
        if group:
            group.is_active = active
            await session.commit()


async def list_active_groups() -> list[Group]:
    async with async_session() as session:
        result = await session.execute(select(Group).where(Group.is_active.is_(True)))
        return list(result.scalars().all())


async def update_group_settings(group_id: int, **kwargs) -> Group | None:
    async with async_session() as session:
        group = await session.get(Group, group_id)
        if group is None:
            return None
        for key, value in kwargs.items():
            setattr(group, key, value)
        await session.commit()
        await session.refresh(group)
        return group


async def toggle_group_setting(group_id: int, field_name: str) -> Group | None:
    async with async_session() as session:
        group = await session.get(Group, group_id)
        if group is None or not hasattr(group, field_name):
            return None
        setattr(group, field_name, not getattr(group, field_name))
        await session.commit()
        await session.refresh(group)
        return group


# ---------- Warnings ----------

async def add_warning(group_id: int, user_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(WarnRecord).where(WarnRecord.group_id == group_id, WarnRecord.user_id == user_id)
        )
        warning = result.scalar_one_or_none()
        if warning is None:
            warning = WarnRecord(group_id=group_id, user_id=user_id, count=1)
            session.add(warning)
        else:
            warning.count += 1
        await session.commit()
        return warning.count


async def reset_warning(group_id: int, user_id: int) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(WarnRecord).where(WarnRecord.group_id == group_id, WarnRecord.user_id == user_id)
        )
        warning = result.scalar_one_or_none()
        if warning:
            await session.delete(warning)
            await session.commit()


async def get_warning_count(group_id: int, user_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(WarnRecord).where(WarnRecord.group_id == group_id, WarnRecord.user_id == user_id)
        )
        warning = result.scalar_one_or_none()
        return warning.count if warning else 0


# ---------- Bad words ----------

async def add_bad_word(group_id: int, word: str) -> bool:
    word = word.strip().lower()
    async with async_session() as session:
        result = await session.execute(
            select(BadWord).where(BadWord.group_id == group_id, BadWord.word == word)
        )
        if result.scalar_one_or_none():
            return False
        session.add(BadWord(group_id=group_id, word=word))
        await session.commit()
        return True


async def remove_bad_word(group_id: int, word: str) -> bool:
    word = word.strip().lower()
    async with async_session() as session:
        result = await session.execute(
            select(BadWord).where(BadWord.group_id == group_id, BadWord.word == word)
        )
        bad_word = result.scalar_one_or_none()
        if bad_word is None:
            return False
        await session.delete(bad_word)
        await session.commit()
        return True


async def list_bad_words(group_id: int) -> list[str]:
    async with async_session() as session:
        result = await session.execute(select(BadWord.word).where(BadWord.group_id == group_id))
        return list(result.scalars().all())


# ---------- Force-subscribe channels ----------

async def add_force_sub_channel(chat_id: str, title: str | None, invite_link: str | None) -> ForceSubChannel:
    async with async_session() as session:
        channel = ForceSubChannel(chat_id=chat_id, title=title, invite_link=invite_link)
        session.add(channel)
        await session.commit()
        await session.refresh(channel)
        return channel


async def remove_force_sub_channel(chat_id: str) -> bool:
    async with async_session() as session:
        result = await session.execute(select(ForceSubChannel).where(ForceSubChannel.chat_id == chat_id))
        channel = result.scalar_one_or_none()
        if channel is None:
            return False
        await session.delete(channel)
        await session.commit()
        return True


async def remove_force_sub_channel_by_id(channel_id: int) -> bool:
    async with async_session() as session:
        channel = await session.get(ForceSubChannel, channel_id)
        if channel is None:
            return False
        await session.delete(channel)
        await session.commit()
        return True


async def list_force_sub_channels() -> list[ForceSubChannel]:
    async with async_session() as session:
        result = await session.execute(select(ForceSubChannel))
        return list(result.scalars().all())


# ---------- Captcha ----------

async def create_pending_captcha(
    group_id: int, user_id: int, message_id: int, deadline: datetime, answer: str
) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(PendingCaptcha).where(
                PendingCaptcha.group_id == group_id, PendingCaptcha.user_id == user_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            await session.delete(existing)
            await session.flush()
        session.add(
            PendingCaptcha(
                group_id=group_id,
                user_id=user_id,
                message_id=message_id,
                deadline=deadline,
                answer=answer,
            )
        )
        await session.commit()


async def get_pending_captcha(group_id: int, user_id: int) -> PendingCaptcha | None:
    async with async_session() as session:
        result = await session.execute(
            select(PendingCaptcha).where(
                PendingCaptcha.group_id == group_id, PendingCaptcha.user_id == user_id
            )
        )
        return result.scalar_one_or_none()


async def delete_pending_captcha(group_id: int, user_id: int) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(PendingCaptcha).where(
                PendingCaptcha.group_id == group_id, PendingCaptcha.user_id == user_id
            )
        )
        pending = result.scalar_one_or_none()
        if pending:
            await session.delete(pending)
            await session.commit()


async def list_expired_captchas(now: datetime) -> list[PendingCaptcha]:
    async with async_session() as session:
        result = await session.execute(select(PendingCaptcha).where(PendingCaptcha.deadline <= now))
        return list(result.scalars().all())
