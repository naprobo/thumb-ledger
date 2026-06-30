"""
交易业务规则、汇总与导出工具。
"""
import csv
import io
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Sequence

from fastapi import HTTPException, status
from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ledger import Category, Ledger, Subject
from app.models.preference import CustomTag
from app.models.transaction import Transaction, TransactionItem, TransactionSubject
from app.models.user import User
from app.schemas.transaction import TransactionCreateRequest, TransactionItemRequest, TransactionUpdateRequest
from app.services.preference import increment_count

DEFAULT_RECEIPT_CATEGORY = "category.other"
MAX_TRANSACTION_PAGE_SIZE = 50


def clamp_page_size(page_size: int) -> int:
    return min(max(page_size, 1), MAX_TRANSACTION_PAGE_SIZE)


def effective_necessity(necessity_step_mode: str, requested_necessity: str | None) -> str:
    if necessity_step_mode == "disabled":
        return "essential"
    return requested_necessity or "essential"


def sort_transactions_by_date_desc(transactions: Sequence[Transaction]) -> list[Transaction]:
    return sorted(transactions, key=lambda transaction: transaction.transaction_date, reverse=True)


def validate_item_mode_payload(ledger: Ledger, payload: TransactionCreateRequest | TransactionUpdateRequest) -> None:
    if ledger.entry_mode == "item" and payload.items is not None and len(payload.items) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Item entry mode requires at least one item.",
        )


def validate_location_payload(
    ledger: Ledger,
    payload: TransactionCreateRequest | TransactionUpdateRequest,
    *,
    creating: bool = False,
) -> None:
    if ledger.location_step_mode == "required":
        if creating and not payload.location_name and not payload.location_tag_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Spending location is required.",
            )
        if (
            "location_name" in payload.model_fields_set
            and not payload.location_name
            and not payload.location_tag_id
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Spending location is required.",
            )


def ensure_item_total_matches_transaction(
    amount: int,
    items: Sequence[TransactionItemRequest | TransactionItem],
) -> None:
    if not items:
        return
    item_total = sum(item.amount for item in items)
    if item_total != amount:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Item amounts must sum to transaction amount.",
        )


async def get_category_snapshot(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    item: TransactionItemRequest,
) -> tuple[uuid.UUID | None, str]:
    if item.category_id is not None:
        category = await db.scalar(
            select(Category).where(Category.id == item.category_id, Category.ledger_id == ledger_id)
        )
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return category.id, category.name
    if item.category_name is not None:
        category = await db.scalar(
            select(Category).where(Category.ledger_id == ledger_id, Category.name == item.category_name)
        )
        return (category.id if category else None), item.category_name
    return await get_default_receipt_category(db, ledger_id)


async def get_default_receipt_category(db: AsyncSession, ledger_id: uuid.UUID) -> tuple[uuid.UUID | None, str]:
    category = await db.scalar(
        select(Category).where(Category.ledger_id == ledger_id, Category.name == DEFAULT_RECEIPT_CATEGORY)
    )
    return (category.id if category else None), DEFAULT_RECEIPT_CATEGORY


async def build_transaction_items(
    db: AsyncSession,
    ledger: Ledger,
    payload_items: list[TransactionItemRequest],
    total_amount: int,
    currency_code: str,
) -> list[TransactionItem]:
    source_items = payload_items
    if not source_items:
        category_id, category_name = await get_default_receipt_category(db, ledger.id)
        return [
            TransactionItem(
                category_id=category_id,
                category_name_snapshot=category_name,
                amount=total_amount,
                currency_code=currency_code,
            )
        ]

    items: list[TransactionItem] = []
    for item in source_items:
        category_id, category_name = await get_category_snapshot(db, ledger.id, item)
        item_tag = None
        item_name = item.item_name
        if item.item_tag_id is not None:
            item_tag = await validate_custom_tag(
                db,
                ledger.id,
                item.item_tag_id,
                "item",
                category_name,
            )
            item_name = item_tag.name
        items.append(
            TransactionItem(
                category_id=category_id,
                category_name_snapshot=category_name,
                item_name=item_name,
                item_tag_id=item_tag.id if item_tag else None,
                amount=item.amount,
                currency_code=item.currency_code or currency_code,
            )
        )
    return items


async def validate_custom_tag(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    tag_id: uuid.UUID,
    tag_type: str,
    scope: str = "",
) -> CustomTag:
    tag = await db.scalar(
        select(CustomTag).where(
            CustomTag.id == tag_id,
            CustomTag.ledger_id == ledger_id,
            CustomTag.tag_type == tag_type,
            CustomTag.scope == scope,
            CustomTag.is_hidden.is_(False),
        )
    )
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom tag not found")
    return tag


async def validate_subjects(db: AsyncSession, ledger: Ledger, subject_ids: list[uuid.UUID]) -> list[Subject]:
    if not subject_ids:
        return []
    result = await db.execute(
        select(Subject).where(
            Subject.ledger_id == ledger.id,
            Subject.id.in_(subject_ids),
            Subject.is_hidden.is_(False),
        )
    )
    subjects = list(result.scalars().all())
    if len(subjects) != len(set(subject_ids)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return subjects


async def update_preferences_for_transaction(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
    transaction: Transaction,
) -> None:
    seen_categories: set[str] = set()
    for item in transaction.items:
        if item.category_name_snapshot not in seen_categories:
            await increment_count(db, ledger_id, user_id, "category", item.category_name_snapshot)
            seen_categories.add(item.category_name_snapshot)
        if item.item_name:
            await increment_count(
                db,
                ledger_id,
                user_id,
                "item",
                item.item_name,
                category=item.category_name_snapshot,
            )
    for transaction_subject in transaction.transaction_subjects:
        await increment_count(db, ledger_id, user_id, "subject", transaction_subject.subject.name)
    if transaction.location_name:
        await increment_count(db, ledger_id, user_id, "location", transaction.location_name)


def transaction_select_with_children() -> Select[tuple[Transaction]]:
    return select(Transaction).options(
        selectinload(Transaction.items),
        selectinload(Transaction.transaction_subjects).selectinload(TransactionSubject.subject),
    )


async def get_transaction_or_404(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    transaction_id: uuid.UUID,
) -> Transaction:
    transaction = await db.scalar(
        transaction_select_with_children().where(
            Transaction.id == transaction_id,
            Transaction.ledger_id == ledger_id,
        )
    )
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date


def resolve_date_range(time_range: str, start_date: date | None, end_date: date | None, today: date | None = None) -> DateRange:
    today = today or date.today()
    if time_range == "week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
    elif time_range == "month":
        start = today.replace(day=1)
        next_month = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
        end = next_month - timedelta(days=1)
    elif time_range == "year":
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)
    else:
        if start_date is None or end_date is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Custom range requires start_date and end_date")
        start = start_date
        end = end_date
    if start > end:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date range")
    return DateRange(start=start, end=end)


def date_filter(ledger_id: uuid.UUID, date_range: DateRange):
    return and_(
        Transaction.ledger_id == ledger_id,
        Transaction.transaction_date >= date_range.start,
        Transaction.transaction_date <= date_range.end,
    )


def category_totals_from_rows(rows: Iterable[tuple[str, str, int]]) -> dict[tuple[str, str], int]:
    totals: dict[tuple[str, str], int] = defaultdict(int)
    for category, currency_code, amount in rows:
        totals[(category, currency_code)] += amount
    return dict(totals)


def transactions_in_date_range(transactions: Sequence[Transaction], date_range: DateRange) -> list[Transaction]:
    return [
        transaction
        for transaction in transactions
        if date_range.start <= transaction.transaction_date <= date_range.end
    ]


async def list_transactions_for_export(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    date_range: DateRange,
) -> list[Transaction]:
    result = await db.execute(
        transaction_select_with_children()
        .where(date_filter(ledger_id, date_range))
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
    )
    return list(result.scalars().unique().all())


def format_transactions_csv(transactions: Sequence[Transaction], recorded_by_lookup: dict[uuid.UUID, str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "date",
            "amount",
            "currency_code",
            "category",
            "item_name",
            "location",
            "subject",
            "necessity",
            "note",
            "recorded_by",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    for transaction in transactions:
        subject = ";".join(ts.subject.name for ts in transaction.transaction_subjects)
        recorded_by = recorded_by_lookup.get(transaction.recorded_by, "") if transaction.recorded_by else ""
        for item in transaction.items:
            writer.writerow(
                {
                    "date": transaction.transaction_date.isoformat(),
                    "amount": item.amount,
                    "currency_code": item.currency_code,
                    "category": item.category_name_snapshot,
                    "item_name": item.item_name or "",
                    "location": transaction.location_name or "",
                    "subject": subject,
                    "necessity": transaction.necessity,
                    "note": transaction.note or "",
                    "recorded_by": recorded_by,
                }
            )
    return output.getvalue()


async def recorded_by_lookup(db: AsyncSession, transactions: Sequence[Transaction]) -> dict[uuid.UUID, str]:
    user_ids = {transaction.recorded_by for transaction in transactions if transaction.recorded_by is not None}
    if not user_ids:
        return {}
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    return {user.id: user.email for user in result.scalars().all()}
