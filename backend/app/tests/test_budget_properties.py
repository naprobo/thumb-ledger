"""
预算模块属性测试（Properties 22, 23）
"""
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.budget import (
    BUDGET_WARNING_OVER,
    BUDGET_WARNING_SOFT,
    allocate_default_category_budgets,
    budget_warning_for_progress,
    default_annual_total,
)


@given(
    monthly_total=st.integers(min_value=1, max_value=10_000_000),
    categories=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=20, unique=True),
)
@settings(max_examples=100)
def test_property_22_default_category_budget_allocation_is_equal_floor(
    monthly_total: int,
    categories: list[str],
) -> None:
    allocations = allocate_default_category_budgets(monthly_total, categories)

    assert set(allocations) == set(categories)
    assert all(amount == monthly_total // len(categories) for amount in allocations.values())


@given(monthly_total=st.integers(min_value=1, max_value=10_000_000))
@settings(max_examples=100)
def test_property_23_budget_warning_thresholds(monthly_total: int) -> None:
    below_soft = max(0, (monthly_total * 80 - 1) // 100)
    at_soft = (monthly_total * 80 + 99) // 100

    assert budget_warning_for_progress(below_soft, monthly_total) is None
    assert budget_warning_for_progress(at_soft, monthly_total) == BUDGET_WARNING_SOFT
    assert budget_warning_for_progress(monthly_total + 1, monthly_total) == BUDGET_WARNING_OVER


@given(monthly_total=st.integers(min_value=1, max_value=10_000_000))
@settings(max_examples=50)
def test_annual_budget_defaults_to_monthly_times_twelve(monthly_total: int) -> None:
    assert default_annual_total(monthly_total, None) == monthly_total * 12
    assert default_annual_total(monthly_total, monthly_total) == monthly_total

