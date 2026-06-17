"""
预算业务规则与进度计算。
"""
import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget, BudgetCategory
from app.models.ledger import Category, Ledger
from app.models.transaction import Transaction, TransactionItem

BUDGET_WARNING_SOFT = "soft"
BUDGET_WARNING_OVER = "over"


def default_annual_total(monthly_total: int, annual_total: int | None) -> int:
    return annual_total if annual_total is not None else monthly_total * 12


def allocate_default_category_budgets(monthly_total: int, categories: list[str]) -> dict[str, int]:
    if not categories:
        return {}
    amount = monthly_total // len(categories)
    return {category: amount for category in categories}


def budget_warning_for_progress(monthly_spent: int, monthly_total: int) -> str | None:
    if monthly_spent > monthly_total:
        return BUDGET_WARNING_OVER
    if monthly_spent * 100 >= monthly_total * 80:
        return BUDGET_WARNING_SOFT
    return None


def current_month_range(today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    start = today.replace(day=1)
    next_month = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
    return start, next_month - timedelta(days=1)


async def active_category_names(db: AsyncSession, ledger_id: uuid.UUID) -> list[str]:
    result = await db.execute(
        select(Category.name).where(Category.ledger_id == ledger_id).order_by(Category.display_order.asc())
    )
    return list(result.scalars().all())


async def monthly_spending(db: AsyncSession, ledger: Ledger, today: date | None = None) -> int:
    start, end = current_month_range(today)
    total = await db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.ledger_id == ledger.id,
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
            Transaction.currency_code == ledger.default_currency_code,
        )
    )
    return int(total or 0)


async def monthly_category_spending(db: AsyncSession, ledger: Ledger, today: date | None = None) -> dict[str, int]:
    start, end = current_month_range(today)
    result = await db.execute(
        select(TransactionItem.category_name_snapshot, func.coalesce(func.sum(TransactionItem.amount), 0))
        .join(Transaction, Transaction.id == TransactionItem.transaction_id)
        .where(
            Transaction.ledger_id == ledger.id,
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
            TransactionItem.currency_code == ledger.default_currency_code,
        )
        .group_by(TransactionItem.category_name_snapshot)
    )
    return {category: int(amount or 0) for category, amount in result.all()}


async def budget_warning_after_transaction(db: AsyncSession, ledger: Ledger) -> str | None:
    if not ledger.budget_enabled:
        return None
    budget = await db.scalar(select(Budget).where(Budget.ledger_id == ledger.id, Budget.is_enabled.is_(True)))
    if budget is None:
        return None
    spent = await monthly_spending(db, ledger)
    return budget_warning_for_progress(spent, budget.monthly_total)


def replace_budget_categories(budget: Budget, allocations: dict[str, int]) -> None:
    budget.categories.clear()
    for category, amount in allocations.items():
        budget.categories.append(BudgetCategory(category=category, amount=amount))
