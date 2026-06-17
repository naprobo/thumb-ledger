"""
交易核心流程 API 路由
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.ledger import Subject
from app.models.transaction import Transaction, TransactionItem, TransactionSubject
from app.models.user import User
from app.schemas.transaction import (
    LedgerSummaryResponse,
    SummaryGroup,
    TimeRange,
    TransactionCreateRequest,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdateRequest,
)
from app.services.auth import get_current_user
from app.services.budget import budget_warning_after_transaction
from app.services.image_storage import delete_stored_images, get_image_storage
from app.services.ledger import get_ledger_or_404, require_read_ledger, require_write_ledger
from app.services.transaction import (
    build_transaction_items,
    clamp_page_size,
    date_filter,
    effective_necessity,
    ensure_item_total_matches_transaction,
    format_transactions_csv,
    get_transaction_or_404,
    list_transactions_for_export,
    recorded_by_lookup,
    resolve_date_range,
    transaction_select_with_children,
    update_preferences_for_transaction,
    validate_item_mode_payload,
    validate_subjects,
)

router = APIRouter(prefix="/ledgers/{ledger_id}", tags=["transactions"])


@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    ledger_id: uuid.UUID,
    payload: TransactionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Transaction:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    validate_item_mode_payload(ledger, payload)
    ensure_item_total_matches_transaction(payload.amount, payload.items)

    currency_code = payload.currency_code or ledger.default_currency_code
    transaction = Transaction(
        ledger_id=ledger_id,
        recorded_by=current_user.id,
        entry_mode_snapshot=ledger.entry_mode,
        amount=payload.amount,
        currency_code=currency_code,
        transaction_date=payload.transaction_date or date.today(),
        necessity=effective_necessity(ledger.necessity_step_mode, payload.necessity),
        note=payload.note,
    )
    transaction.items = await build_transaction_items(db, ledger, payload.items, payload.amount, currency_code)
    subjects = await validate_subjects(db, ledger, payload.subject_ids)
    transaction.transaction_subjects = [TransactionSubject(subject_id=subject.id, subject=subject) for subject in subjects]
    db.add(transaction)
    await db.flush()
    await update_preferences_for_transaction(db, ledger_id, current_user.id, transaction)
    transaction.budget_warning = await budget_warning_after_transaction(db, ledger)
    return transaction


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    ledger_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1),
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    page_size = clamp_page_size(page_size)
    offset = (page - 1) * page_size
    filters = [Transaction.ledger_id == ledger_id]
    if start_date is not None:
        filters.append(Transaction.transaction_date >= start_date)
    if end_date is not None:
        filters.append(Transaction.transaction_date <= end_date)

    total = await db.scalar(select(func.count()).select_from(Transaction).where(*filters))
    result = await db.execute(
        transaction_select_with_children()
        .where(*filters)
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    transactions = list(result.scalars().unique().all())
    page_totals: dict[str, int] = {}
    for transaction in transactions:
        page_totals[transaction.currency_code] = page_totals.get(transaction.currency_code, 0) + transaction.amount

    return TransactionListResponse(
        items=transactions,
        page=page,
        page_size=page_size,
        total=total or 0,
        page_total_amounts=page_totals,
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    ledger_id: uuid.UUID,
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Transaction:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    return await get_transaction_or_404(db, ledger_id, transaction_id)


@router.patch("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    ledger_id: uuid.UUID,
    transaction_id: uuid.UUID,
    payload: TransactionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Transaction:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    validate_item_mode_payload(ledger, payload)
    transaction = await get_transaction_or_404(db, ledger_id, transaction_id)

    if payload.amount is not None:
        transaction.amount = payload.amount
    if payload.currency_code is not None:
        transaction.currency_code = payload.currency_code
    if payload.transaction_date is not None:
        transaction.transaction_date = payload.transaction_date
    if payload.necessity is not None or ledger.necessity_step_mode == "disabled":
        transaction.necessity = effective_necessity(ledger.necessity_step_mode, payload.necessity)
    if "note" in payload.model_fields_set:
        transaction.note = payload.note

    if payload.items is not None:
        transaction.items.clear()
        currency_code = transaction.currency_code
        amount = transaction.amount
        transaction.items.extend(await build_transaction_items(db, ledger, payload.items, amount, currency_code))
    elif ledger.entry_mode == "receipt":
        for item in transaction.items:
            item.amount = transaction.amount
            item.currency_code = transaction.currency_code
    if payload.subject_ids is not None:
        transaction.transaction_subjects.clear()
        subjects = await validate_subjects(db, ledger, payload.subject_ids)
        transaction.transaction_subjects.extend(
            TransactionSubject(subject_id=subject.id, subject=subject) for subject in subjects
        )
    if ledger.entry_mode == "item":
        ensure_item_total_matches_transaction(transaction.amount, transaction.items)
    await db.flush()
    await update_preferences_for_transaction(db, ledger_id, current_user.id, transaction)
    return transaction


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    ledger_id: uuid.UUID,
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    transaction = await get_transaction_or_404(db, ledger_id, transaction_id)
    await db.refresh(transaction, attribute_names=["images"])
    await delete_stored_images(get_image_storage(get_settings()), transaction.images)
    await db.delete(transaction)
    return {"detail": "Transaction deleted successfully."}


@router.get("/summary", response_model=LedgerSummaryResponse)
async def ledger_summary(
    ledger_id: uuid.UUID,
    time_range: TimeRange = Query("month"),
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LedgerSummaryResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    resolved_range = resolve_date_range(time_range, start_date, end_date)

    category_rows = await db.execute(
        select(
            TransactionItem.category_name_snapshot,
            TransactionItem.currency_code,
            func.sum(TransactionItem.amount),
        )
        .join(Transaction, Transaction.id == TransactionItem.transaction_id)
        .where(date_filter(ledger_id, resolved_range))
        .group_by(TransactionItem.category_name_snapshot, TransactionItem.currency_code)
        .order_by(TransactionItem.category_name_snapshot.asc())
    )
    subject_rows = await db.execute(
        select(Subject.name, Transaction.currency_code, func.sum(Transaction.amount))
        .join(TransactionSubject, TransactionSubject.transaction_id == Transaction.id)
        .join(Subject, Subject.id == TransactionSubject.subject_id)
        .where(date_filter(ledger_id, resolved_range))
        .group_by(Subject.name, Transaction.currency_code)
        .order_by(Subject.name.asc())
    )
    necessity_rows = await db.execute(
        select(Transaction.necessity, Transaction.currency_code, func.sum(Transaction.amount))
        .where(date_filter(ledger_id, resolved_range))
        .group_by(Transaction.necessity, Transaction.currency_code)
        .order_by(Transaction.necessity.asc())
    )

    return LedgerSummaryResponse(
        categories=[
            SummaryGroup(key=key, currency_code=currency_code, amount=int(amount))
            for key, currency_code, amount in category_rows.all()
        ],
        subjects=[
            SummaryGroup(key=key, currency_code=currency_code, amount=int(amount))
            for key, currency_code, amount in subject_rows.all()
        ],
        necessities=[
            SummaryGroup(key=key, currency_code=currency_code, amount=int(amount))
            for key, currency_code, amount in necessity_rows.all()
        ],
    )


@router.get("/export")
async def export_transactions(
    ledger_id: uuid.UUID,
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    resolved_range = resolve_date_range("custom", start_date, end_date)
    transactions = await list_transactions_for_export(db, ledger_id, resolved_range)
    csv_body = format_transactions_csv(transactions, await recorded_by_lookup(db, transactions))
    return Response(
        content=csv_body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'},
    )
