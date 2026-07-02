"""
预算 API 路由
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.budget import Budget
from app.models.user import User
from app.schemas.budget import BudgetProgressResponse, BudgetResponse, BudgetUpsertRequest
from app.services.auth import get_current_user
from app.services.budget import (
    active_category_names,
    allocate_default_category_budgets,
    budget_warning_for_progress,
    default_annual_total,
    monthly_category_spending,
    monthly_spending,
    replace_budget_categories,
)
from app.services.ledger import get_ledger_or_404, require_read_ledger, require_write_ledger

router = APIRouter(prefix="/ledgers/{ledger_id}/budget", tags=["budget"])


async def get_budget_with_categories(db: AsyncSession, ledger_id: uuid.UUID) -> Budget | None:
    return await db.scalar(
        select(Budget)
        .options(selectinload(Budget.categories))
        .where(Budget.ledger_id == ledger_id, Budget.is_enabled.is_(True))
    )


async def build_budget_response(
    db: AsyncSession,
    budget: Budget,
    target_month: date | None = None,
) -> BudgetResponse:
    ledger = await get_ledger_or_404(db, budget.ledger_id)
    spent = await monthly_spending(db, ledger, today=target_month)
    progress = BudgetProgressResponse(
        monthly_spent=spent,
        monthly_total=budget.monthly_total,
        percentage=spent / budget.monthly_total if budget.monthly_total else 0,
        warning=budget_warning_for_progress(spent, budget.monthly_total),
        category_spending=await monthly_category_spending(db, ledger, today=target_month),
    )
    return BudgetResponse(
        id=budget.id,
        ledger_id=budget.ledger_id,
        monthly_total=budget.monthly_total,
        annual_total=budget.annual_total,
        is_enabled=budget.is_enabled,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
        categories=budget.categories,
        progress=progress,
    )


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def upsert_budget(
    ledger_id: uuid.UUID,
    payload: BudgetUpsertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BudgetResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    budget = await get_budget_with_categories(db, ledger_id)
    if budget is None:
        budget = Budget(ledger_id=ledger_id, monthly_total=payload.monthly_total, categories=[])
        db.add(budget)

    budget.monthly_total = payload.monthly_total
    budget.annual_total = default_annual_total(payload.monthly_total, payload.annual_total)
    budget.is_enabled = True
    ledger.budget_enabled = True

    if payload.categories is None:
        allocations = allocate_default_category_budgets(
            payload.monthly_total,
            await active_category_names(db, ledger_id),
        )
    else:
        allocations = {item.category: item.amount for item in payload.categories}
    replace_budget_categories(budget, allocations)
    await db.flush()
    refreshed_budget = await get_budget_with_categories(db, ledger_id)
    if refreshed_budget is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Budget reload failed")
    return await build_budget_response(db, refreshed_budget)


@router.get("", response_model=BudgetResponse)
async def get_budget(
    ledger_id: uuid.UUID,
    target_month: date | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BudgetResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    budget = await get_budget_with_categories(db, ledger_id)
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return await build_budget_response(db, budget, target_month=target_month)


@router.delete("")
async def disable_budget(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    budget = await get_budget_with_categories(db, ledger_id)
    if budget is not None:
        budget.is_enabled = False
    ledger.budget_enabled = False
    await db.flush()
    return {"detail": "Budget disabled successfully."}
