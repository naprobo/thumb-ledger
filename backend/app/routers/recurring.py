"""
定期交易模板 API 路由
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.recurring import RecurringTransaction
from app.models.user import User
from app.schemas.recurring import RecurringCreateRequest, RecurringResponse, RecurringUpdateRequest
from app.services.auth import get_current_user
from app.services.ledger import get_ledger_or_404, require_read_ledger, require_write_ledger
from app.services.recurring import serialize_template_data

router = APIRouter(prefix="/ledgers/{ledger_id}/recurring", tags=["recurring"])


async def get_recurring_or_404(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    recurring_id: uuid.UUID,
) -> RecurringTransaction:
    recurring = await db.scalar(
        select(RecurringTransaction).where(
            RecurringTransaction.id == recurring_id,
            RecurringTransaction.ledger_id == ledger_id,
        )
    )
    if recurring is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction not found")
    return recurring


@router.post("", response_model=RecurringResponse, status_code=status.HTTP_201_CREATED)
async def create_recurring(
    ledger_id: uuid.UUID,
    payload: RecurringCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecurringTransaction:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    recurring = RecurringTransaction(
        ledger_id=ledger_id,
        created_by=current_user.id,
        interval=payload.interval,
        next_run_date=payload.next_run_date,
        is_active=True,
        template_data=serialize_template_data(payload.template_data),
    )
    db.add(recurring)
    await db.flush()
    return recurring


@router.get("", response_model=list[RecurringResponse])
async def list_recurring(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecurringTransaction]:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    result = await db.execute(
        select(RecurringTransaction)
        .where(RecurringTransaction.ledger_id == ledger_id)
        .order_by(RecurringTransaction.is_active.desc(), RecurringTransaction.next_run_date.asc())
    )
    return list(result.scalars().all())


@router.patch("/{recurring_id}", response_model=RecurringResponse)
async def update_recurring(
    ledger_id: uuid.UUID,
    recurring_id: uuid.UUID,
    payload: RecurringUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecurringTransaction:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    recurring = await get_recurring_or_404(db, ledger_id, recurring_id)
    if payload.interval is not None:
        recurring.interval = payload.interval
    if payload.next_run_date is not None:
        recurring.next_run_date = payload.next_run_date
    if payload.is_active is not None:
        recurring.is_active = payload.is_active
    if payload.template_data is not None:
        recurring.template_data = serialize_template_data(payload.template_data)
    await db.flush()
    await db.refresh(recurring)
    return recurring


@router.delete("/{recurring_id}")
async def delete_recurring(
    ledger_id: uuid.UUID,
    recurring_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    recurring = await get_recurring_or_404(db, ledger_id, recurring_id)
    await db.delete(recurring)
    await db.flush()
    return {"detail": "Recurring transaction deleted successfully."}
