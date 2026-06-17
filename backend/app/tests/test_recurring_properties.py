"""
定期交易调度测试。
"""
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import inspect

from app.models.transaction import Transaction
from app.schemas.recurring import RecurringTemplateData
from app.services.recurring import (
    ledger_today,
    next_run_after,
    serialize_template_data,
)


@pytest.mark.parametrize(
    ("current", "interval", "expected"),
    [
        (date(2026, 1, 1), "daily", date(2026, 1, 2)),
        (date(2026, 1, 1), "weekly", date(2026, 1, 8)),
        (date(2026, 1, 31), "monthly", date(2026, 2, 28)),
        (date(2024, 2, 29), "yearly", date(2025, 2, 28)),
    ],
)
def test_recurring_next_run_date_advances_by_interval(
    current: date,
    interval: str,
    expected: date,
) -> None:
    assert next_run_after(current, interval) == expected


def test_recurring_uses_ledger_timezone_for_due_date() -> None:
    now_utc = datetime(2026, 6, 11, 15, 0, tzinfo=timezone.utc)

    assert ledger_today("Asia/Tokyo", now_utc) == date(2026, 6, 12)
    assert ledger_today("UTC", now_utc) == date(2026, 6, 11)


def test_recurring_template_serialization_drops_fixed_transaction_date() -> None:
    template = RecurringTemplateData(
        amount=1200,
        currency_code="JPY",
        necessity="essential",
        note="rent",
    )

    data = serialize_template_data(template)

    assert data["amount"] == 1200
    assert data["currency_code"] == "JPY"
    assert "transaction_date" not in data


def test_delete_recurring_template_retains_generated_transactions() -> None:
    recurring_relationship = inspect(Transaction).relationships["recurring_transaction"]

    assert recurring_relationship.local_columns.pop().foreign_keys.pop().ondelete == "SET NULL"

