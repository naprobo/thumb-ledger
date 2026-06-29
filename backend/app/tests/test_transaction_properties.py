"""
交易核心流程属性测试（Properties 11, 13, 15, 16, 17, 26）
"""
import uuid
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.ledger import Ledger, LedgerMember
from app.models.transaction import TransactionItem
from app.models.user import User
from app.services.ledger import can_write_ledger
from app.services.transaction import (
    DateRange,
    MAX_TRANSACTION_PAGE_SIZE,
    category_totals_from_rows,
    clamp_page_size,
    effective_necessity,
    ensure_item_total_matches_transaction,
    format_transactions_csv,
    sort_transactions_by_date_desc,
    transactions_in_date_range,
)


@given(
    offsets=st.lists(st.integers(min_value=-3650, max_value=3650), min_size=2, max_size=100),
)
@settings(max_examples=100)
def test_property_15_transaction_list_ordered_by_date_desc(offsets: list[int]) -> None:
    base = date(2026, 1, 1)
    transactions = [
        SimpleNamespace(transaction_date=base + timedelta(days=offset))
        for offset in offsets
    ]

    result = sort_transactions_by_date_desc(transactions)
    dates = [transaction.transaction_date for transaction in result]

    assert dates == sorted(dates, reverse=True)


@given(page_size=st.integers(min_value=-100, max_value=500))
@settings(max_examples=100)
def test_property_16_transaction_page_size_never_exceeds_50(page_size: int) -> None:
    assert 1 <= clamp_page_size(page_size) <= MAX_TRANSACTION_PAGE_SIZE


@given(requested=st.sampled_from(["essential", "non-essential", None]))
@settings(max_examples=20)
def test_property_11_disabled_necessity_step_forces_essential(requested: str | None) -> None:
    assert effective_necessity("disabled", requested) == "essential"


class _FakeDb:
    def __init__(self, member: LedgerMember | None) -> None:
        self.member = member

    async def scalar(self, _query):
        return self.member


@pytest.mark.asyncio
async def test_property_13_read_only_member_cannot_write_transactions() -> None:
    ledger_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    readonly_user_id = uuid.uuid4()
    ledger = Ledger(id=ledger_id, owner_id=owner_id, name="home", entry_mode="receipt")
    readonly_user = User(id=readonly_user_id, email="readonly@example.com", password_hash="hash")
    member = LedgerMember(ledger_id=ledger_id, user_id=readonly_user_id, role="read-only")

    assert await can_write_ledger(_FakeDb(member), ledger, readonly_user) is False


@given(
    amounts=st.lists(st.integers(min_value=1, max_value=1_000_000), min_size=1, max_size=50),
    categories=st.lists(st.sampled_from(["食物", "交通", "其他"]), min_size=1, max_size=50),
    currencies=st.lists(st.sampled_from(["JPY", "USD"]), min_size=1, max_size=50),
)
@settings(max_examples=100)
def test_property_17_category_summary_amount_correctness(
    amounts: list[int],
    categories: list[str],
    currencies: list[str],
) -> None:
    rows = [
        (categories[index % len(categories)], currencies[index % len(currencies)], amount)
        for index, amount in enumerate(amounts)
    ]

    totals = category_totals_from_rows(rows)

    assert sum(totals.values()) == sum(amounts)
    for currency in set(currencies):
        expected = sum(amount for category, row_currency, amount in rows if row_currency == currency)
        actual = sum(amount for (_category, row_currency), amount in totals.items() if row_currency == currency)
        assert actual == expected


@given(amounts=st.lists(st.integers(min_value=1, max_value=1_000_000), min_size=1, max_size=20))
@settings(max_examples=100)
def test_item_amounts_must_match_transaction_total(amounts: list[int]) -> None:
    items = [
        TransactionItem(amount=amount, currency_code="JPY", category_name_snapshot="食物")
        for amount in amounts
    ]

    ensure_item_total_matches_transaction(sum(amounts), items)
    with pytest.raises(Exception):
        ensure_item_total_matches_transaction(sum(amounts) + 1, items)


def test_property_26_csv_export_contains_exact_date_range_rows() -> None:
    ledger_id = uuid.uuid4()
    recorder_id = uuid.uuid4()
    transactions = [
        _transaction(ledger_id, recorder_id, date(2026, 1, 1), 100, "食物"),
        _transaction(ledger_id, recorder_id, date(2026, 1, 15), 200, "交通"),
        _transaction(ledger_id, recorder_id, date(2026, 2, 1), 300, "其他"),
    ]
    date_range = DateRange(start=date(2026, 1, 1), end=date(2026, 1, 31))

    filtered = transactions_in_date_range(transactions, date_range)
    csv_body = format_transactions_csv(filtered, {recorder_id: "user@example.com"})

    assert len(filtered) == 2
    assert "2026-01-01,100,JPY,食物" in csv_body
    assert "2026-01-15,200,JPY,交通" in csv_body
    assert "2026-02-01" not in csv_body


def _transaction(
    ledger_id: uuid.UUID,
    recorder_id: uuid.UUID,
    transaction_date: date,
    amount: int,
    category: str,
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        ledger_id=ledger_id,
        recorded_by=recorder_id,
        amount=amount,
        currency_code="JPY",
        transaction_date=transaction_date,
        necessity="essential",
        note="",
        location_name="",
        items=[
            SimpleNamespace(
                amount=amount,
                currency_code="JPY",
                category_name_snapshot=category,
                item_name="",
            )
        ],
        transaction_subjects=[],
    )
