"""
账本模块属性测试（Properties 6-9, 14, 19）
"""
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError
from sqlalchemy import inspect

from app.models.ledger import Ledger
from app.schemas.ledger import LedgerCreateRequest
from app.services.currency import SUPPORTED_CURRENCY_CODES
from app.services.ledger import (
    DEFAULT_CATEGORIES,
    DEFAULT_SUBJECTS,
    MAX_LEDGERS_PER_USER,
    MAX_SHARED_MEMBERS_PER_LEDGER,
    MAX_SUBJECTS_PER_LEDGER,
    can_add_subject,
    can_create_more_ledgers,
    can_modify_preset_subject,
    can_modify_system_category,
)


@given(name=st.text(min_size=0, max_size=80))
@settings(max_examples=100)
def test_property_6_ledger_name_length_constraint(name: str) -> None:
    if 1 <= len(name) <= 50:
        request = LedgerCreateRequest(name=name, entry_mode="receipt")
        assert request.name == name
    else:
        try:
            LedgerCreateRequest(name=name, entry_mode="receipt")
        except ValidationError:
            return
        raise AssertionError("Invalid ledger name length was accepted")


@given(count=st.integers(min_value=0, max_value=20))
@settings(max_examples=50)
def test_property_7_ledger_count_limit(count: int) -> None:
    assert can_create_more_ledgers(count) is (count < MAX_LEDGERS_PER_USER)


@given(count=st.integers(min_value=0, max_value=30))
@settings(max_examples=50)
def test_property_8_subject_count_limit(count: int) -> None:
    assert can_add_subject(count) is (count < MAX_SUBJECTS_PER_LEDGER)


@given(is_preset=st.booleans())
@settings(max_examples=10)
def test_property_9_preset_subject_cannot_be_deleted(is_preset: bool) -> None:
    assert can_modify_preset_subject(is_preset) is (not is_preset)


@given(is_system=st.booleans())
@settings(max_examples=10)
def test_system_category_cannot_be_modified(is_system: bool) -> None:
    assert can_modify_system_category(is_system) is (not is_system)


@given(count=st.integers(min_value=0, max_value=20))
@settings(max_examples=50)
def test_property_14_shared_member_count_limit(count: int) -> None:
    assert (count < MAX_SHARED_MEMBERS_PER_LEDGER) is (count <= 9)


def test_property_19_ledger_delete_cascades_owned_data() -> None:
    relationships = inspect(Ledger).relationships

    assert "delete-orphan" in relationships["members"].cascade
    assert "delete-orphan" in relationships["share_requests"].cascade
    assert "delete-orphan" in relationships["subjects"].cascade
    assert "delete-orphan" in relationships["categories"].cascade
    assert "delete-orphan" in relationships["transactions"].cascade
    assert "delete-orphan" in relationships["budget"].cascade
    assert "delete-orphan" in relationships["preferences"].cascade


def test_default_subjects_and_categories_match_spec() -> None:
    assert DEFAULT_SUBJECTS == [
        "subject.self",
        "subject.dad",
        "subject.mom",
        "subject.child",
        "subject.grandpa",
        "subject.grandma",
        "subject.husband",
        "subject.wife",
        "subject.brother",
        "subject.sister",
    ]
    assert DEFAULT_CATEGORIES == [
        "category.food",
        "category.dining",
        "category.daily",
        "category.clothing",
        "category.housing",
        "category.utilities",
        "category.communication",
        "category.transport",
        "category.vehicle",
        "category.medical",
        "category.insurance",
        "category.education",
        "category.childcare",
        "category.pets",
        "category.entertainment",
        "category.travel",
        "category.digital",
        "category.subscriptions",
        "category.social",
        "category.beauty",
        "category.taxes",
        "category.other",
    ]


def test_default_currency_must_be_supported_selection() -> None:
    request = LedgerCreateRequest(name="Home", entry_mode="receipt", default_currency_code="JPY")
    assert request.default_currency_code == "JPY"
    assert {"JPY", "CNY", "USD", "EUR", "GBP", "KRW"}.issubset(SUPPORTED_CURRENCY_CODES)

    try:
        LedgerCreateRequest(name="Home", entry_mode="receipt", default_currency_code="XXX")
    except ValidationError:
        return
    raise AssertionError("Unsupported currency code was accepted")
