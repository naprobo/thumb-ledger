"""
账本业务规则与权限工具。
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ledger import Category, Ledger, LedgerMember, ShareRequest, Subject
from app.models.notification import Notification
from app.models.user import User
from app.services.catalog import DEFAULT_CATEGORIES, DEFAULT_SUBJECTS

MAX_LEDGERS_PER_USER = 10
MAX_SUBJECTS_PER_LEDGER = 20
MAX_CUSTOM_SUBJECTS_PER_LEDGER = 20
MAX_SHARED_MEMBERS_PER_LEDGER = 10


def can_create_more_ledgers(current_count: int) -> bool:
    return current_count < MAX_LEDGERS_PER_USER


def can_add_subject(current_count: int) -> bool:
    return current_count < MAX_SUBJECTS_PER_LEDGER


def can_add_custom_subject(current_count: int) -> bool:
    return current_count < MAX_CUSTOM_SUBJECTS_PER_LEDGER


def can_modify_preset_subject(is_preset: bool) -> bool:
    return not is_preset


def can_modify_system_category(is_system: bool) -> bool:
    return not is_system


def encode_share_code(ledger_id: uuid.UUID) -> str:
    return ledger_id.hex


def decode_share_code(share_code: str) -> uuid.UUID:
    try:
        return uuid.UUID(hex=share_code)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ledger not found",
        ) from exc


async def get_ledger_or_404(db: AsyncSession, ledger_id: uuid.UUID) -> Ledger:
    ledger = await db.scalar(select(Ledger).where(Ledger.id == ledger_id))
    if ledger is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ledger not found")
    return ledger


async def get_membership(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
) -> LedgerMember | None:
    return await db.scalar(
        select(LedgerMember).where(
            LedgerMember.ledger_id == ledger_id,
            LedgerMember.user_id == user_id,
        )
    )


async def can_read_ledger(db: AsyncSession, ledger: Ledger, user: User) -> bool:
    if ledger.owner_id == user.id:
        return True
    return await get_membership(db, ledger.id, user.id) is not None


async def can_write_ledger(db: AsyncSession, ledger: Ledger, user: User) -> bool:
    if ledger.owner_id == user.id:
        return True
    membership = await get_membership(db, ledger.id, user.id)
    return membership is not None and membership.role == "read-write"


async def require_read_ledger(db: AsyncSession, ledger: Ledger, user: User) -> None:
    if not await can_read_ledger(db, ledger, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ledger access denied")


async def require_write_ledger(db: AsyncSession, ledger: Ledger, user: User) -> None:
    if not await can_write_ledger(db, ledger, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ledger write access denied")


def require_owner(ledger: Ledger, user: User) -> None:
    if ledger.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ledger owner required")


async def ensure_user_can_create_ledger(db: AsyncSession, user_id: uuid.UUID) -> None:
    count = await db.scalar(select(func.count()).select_from(Ledger).where(Ledger.owner_id == user_id))
    if count is not None and not can_create_more_ledgers(count):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Maximum ledger limit reached",
        )


def add_default_subjects(ledger: Ledger) -> None:
    if not ledger.subject_enabled:
        return
    for index, name in enumerate(DEFAULT_SUBJECTS):
        ledger.subjects.append(Subject(name=name, is_preset=True, display_order=index))


def add_default_categories(ledger: Ledger) -> None:
    for index, name in enumerate(DEFAULT_CATEGORIES):
        ledger.categories.append(Category(name=name, is_system=True, display_order=index))


async def add_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    notification_type: str,
    payload: dict | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        payload=payload,
        created_at=datetime.now(timezone.utc),
    )
    db.add(notification)
    await db.flush()
    return notification


async def create_ledger_member(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
    role: str,
) -> LedgerMember:
    member = LedgerMember(
        ledger_id=ledger_id,
        user_id=user_id,
        role=role,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(member)
    await db.flush()
    return member


async def ensure_shared_member_limit(db: AsyncSession, ledger_id: uuid.UUID) -> None:
    count = await db.scalar(
        select(func.count()).select_from(LedgerMember).where(LedgerMember.ledger_id == ledger_id)
    )
    if count is not None and count >= MAX_SHARED_MEMBERS_PER_LEDGER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Maximum shared member limit reached",
        )


async def get_pending_share_request_or_404(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    request_id: uuid.UUID,
) -> ShareRequest:
    share_request = await db.scalar(
        select(ShareRequest).where(
            ShareRequest.id == request_id,
            ShareRequest.ledger_id == ledger_id,
            ShareRequest.status == "pending",
        )
    )
    if share_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share request not found",
        )
    return share_request
