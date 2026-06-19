"""
偏好引擎属性测试（Property 10）
"""
from collections import Counter

from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.catalog import DEFAULT_CATEGORIES, DEFAULT_ITEM_SUGGESTIONS
from app.services.preference import sort_tags_by_preference


@given(
    selections=st.lists(
        st.sampled_from(["subject.self", "subject.dad", "subject.mom", "subject.child", "subject.grandpa"]),
        min_size=1,
        max_size=50,
    )
)
@settings(max_examples=100)
def test_property_10_preference_sort_counts_and_default_tie_breaker(
    selections: list[str],
) -> None:
    default_order = ["subject.self", "subject.dad", "subject.mom", "subject.child", "subject.grandpa"]
    counts = Counter(selections)

    result = sort_tags_by_preference(default_order, counts)

    for previous, current in zip(result, result[1:]):
        assert counts[previous] >= counts[current]
        if counts[previous] == counts[current]:
            assert default_order.index(previous) < default_order.index(current)


def test_default_category_catalog_matches_spec_and_has_item_suggestions() -> None:
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
    for category in DEFAULT_CATEGORIES:
        assert len(DEFAULT_ITEM_SUGGESTIONS[category]) >= 5


def test_selected_categories_sort_by_count_then_default_order() -> None:
    default_order = ["category.food", "category.dining", "category.pets", "category.other"]
    counts = {"category.food": 1, "category.pets": 1, "category.dining": 0, "category.other": 0}

    result = sort_tags_by_preference(default_order, counts)

    assert result == ["category.food", "category.pets", "category.dining", "category.other"]


def test_custom_items_are_sorted_after_defaults_when_unselected() -> None:
    default_order = ["item.rice", "item.eggs", "item.milk"]
    counts = {"custom.manual": 0, "item.eggs": 2}

    result = sort_tags_by_preference([*default_order, "custom.manual"], counts)

    assert result[0] == "item.eggs"
    assert result[-1] == "custom.manual"
