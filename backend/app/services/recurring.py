"""
定期交易模板与调度生成逻辑。
"""
import calendar
import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session_factory
from app.models.ledger import Ledger
from app.models.recurring import RecurringTransaction
from app.models.transaction import Transaction, TransactionSubject
from app.schemas.transaction import TransactionCreateRequest
from app.services.transaction import (
    build_transaction_items,
    effective_necessity,
    ensure_item_total_matches_transaction,
    validate_item_mode_payload,
    validate_subjects,
)

logger = logging.getLogger(__name__)


def add_months(current: date, months: int) -> date:
    month_index = current.month - 1 + months
    year = current.year + month_index // 12
    month = month_index % 12 + 1
    day = min(current.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def next_run_after(current: date, interval: str) -> date:
    if interval == "daily":
        return current + timedelta(days=1)
    if interval == "weekly":
        return current + timedelta(days=7)
    if interval == "monthly":
        return add_months(current, 1)
    if interval == "yearly":
        return add_months(current, 12)
    raise ValueError(f"Unsupported recurring interval: {interval}")


def ledger_today(ledger_timezone: str, now_utc: datetime | None = None) -> date:
    now_utc = now_utc or datetime.now(timezone.utc)
    try:
        zone = ZoneInfo(ledger_timezone)
    except ZoneInfoNotFoundError:
        zone = ZoneInfo("UTC")
    return now_utc.astimezone(zone).date()


def serialize_template_data(payload: TransactionCreateRequest) -> dict:
    data = payload.model_dump(mode="json", exclude_none=True)
    data.pop("transaction_date", None)
    return data


async def create_transaction_from_recurring(
    db: AsyncSession,
    recurring: RecurringTransaction,
    ledger: Ledger,
    run_date: date,
) -> Transaction:
    payload = TransactionCreateRequest(**(recurring.template_data or {}))
    validate_item_mode_payload(ledger, payload)
    ensure_item_total_matches_transaction(payload.amount, payload.items)
    currency_code = payload.currency_code or ledger.default_currency_code

    transaction = Transaction(
        ledger_id=ledger.id,
        recorded_by=recurring.created_by,
        entry_mode_snapshot=ledger.entry_mode,
        amount=payload.amount,
        currency_code=currency_code,
        transaction_date=run_date,
        necessity=effective_necessity(ledger.necessity_step_mode, payload.necessity),
        note=payload.note,
        recurring_transaction_id=recurring.id,
    )
    transaction.items = await build_transaction_items(db, ledger, payload.items, payload.amount, currency_code)
    subjects = await validate_subjects(db, ledger, payload.subject_ids)
    transaction.transaction_subjects = [
        TransactionSubject(subject_id=subject.id, subject=subject)
        for subject in subjects
    ]
    db.add(transaction)
    await db.flush()
    return transaction


async def generate_due_recurring_transactions(
    db: AsyncSession,
    now_utc: datetime | None = None,
) -> int:
    result = await db.execute(
        select(RecurringTransaction)
        .options(selectinload(RecurringTransaction.ledger))
        .where(RecurringTransaction.is_active.is_(True))
        .order_by(RecurringTransaction.next_run_date.asc())
    )
    generated = 0
    for recurring in result.scalars().all():
        ledger = recurring.ledger
        today = ledger_today(ledger.timezone, now_utc)
        while recurring.next_run_date <= today:
            await create_transaction_from_recurring(db, recurring, ledger, recurring.next_run_date)
            recurring.next_run_date = next_run_after(recurring.next_run_date, recurring.interval)
            generated += 1
    return generated


async def run_recurring_generation_once() -> None:
    session_factory = get_session_factory()
    async with session_factory() as db:
        try:
            await generate_due_recurring_transactions(db)
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("Recurring transaction generation failed")


def create_recurring_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=timezone.utc)
    scheduler.add_job(
        run_recurring_generation_once,
        trigger="cron",
        hour=0,
        minute=0,
        id="recurring-transaction-generation",
        replace_existing=True,
    )
    return scheduler
