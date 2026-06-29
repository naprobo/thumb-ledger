"""
偏好引擎服务。
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ledger import Category, HiddenSubject, Subject
from app.models.preference import Preference
from app.services.catalog import DEFAULT_ITEM_SUGGESTIONS


def sort_tags_by_preference(
    default_order: list[str],
    counts: dict[str, int],
) -> list[str]:
    order_index = {value: index for index, value in enumerate(default_order)}
    return sorted(
        default_order,
        key=lambda value: (-counts.get(value, 0), order_index.get(value, len(default_order))),
    )


async def increment_count(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
    tag_type: str,
    tag_value: str,
    category: str | None = None,
) -> Preference:
    preference = await db.scalar(
        select(Preference).where(
            Preference.ledger_id == ledger_id,
            Preference.user_id == user_id,
            Preference.tag_type == tag_type,
            Preference.tag_value == tag_value,
            Preference.category == category,
        )
    )
    if preference is None:
        preference = Preference(
            ledger_id=ledger_id,
            user_id=user_id,
            tag_type=tag_type,
            tag_value=tag_value,
            category=category,
            selection_count=0,
        )
        db.add(preference)

    preference.selection_count += 1
    preference.last_selected_at = datetime.now(timezone.utc)
    await db.flush()
    return preference


async def _get_counts(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
    tag_type: str,
    category: str | None = None,
) -> dict[str, int]:
    conditions = [
        Preference.ledger_id == ledger_id,
        Preference.user_id == user_id,
        Preference.tag_type == tag_type,
    ]
    if category is not None:
        conditions.append(Preference.category == category)

    result = await db.execute(select(Preference).where(*conditions))
    return {preference.tag_value: preference.selection_count for preference in result.scalars().all()}


async def _get_preferences(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
    tag_type: str,
    category: str | None = None,
) -> dict[str, Preference]:
    conditions = [
        Preference.ledger_id == ledger_id,
        Preference.user_id == user_id,
        Preference.tag_type == tag_type,
    ]
    if category is not None:
        conditions.append(Preference.category == category)

    result = await db.execute(select(Preference).where(*conditions))
    return {preference.tag_value: preference for preference in result.scalars().all()}


def visible_subject_filter(ledger_id: uuid.UUID, user_id: uuid.UUID):
    hidden_subjects = select(HiddenSubject.subject_id).where(
        HiddenSubject.ledger_id == ledger_id,
        HiddenSubject.user_id == user_id,
    )
    return Subject.ledger_id == ledger_id, ~Subject.id.in_(hidden_subjects)


async def get_sorted_subjects(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[str]:
    result = await db.execute(
        select(Subject).where(*visible_subject_filter(ledger_id, user_id)).order_by(Subject.display_order.asc())
    )
    subjects = [subject.name for subject in result.scalars().all()]
    counts = await _get_counts(db, ledger_id, user_id, "subject")
    return sort_tags_by_preference(subjects, counts)


async def get_subject_preference_details(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[dict]:
    result = await db.execute(
        select(Subject).where(*visible_subject_filter(ledger_id, user_id)).order_by(Subject.display_order.asc())
    )
    subjects = [subject.name for subject in result.scalars().all()]
    preferences = await _get_preferences(db, ledger_id, user_id, "subject")
    counts = {value: preference.selection_count for value, preference in preferences.items()}
    sorted_subjects = sort_tags_by_preference(subjects, counts)
    return [
        {
            "value": subject,
            "selection_count": preferences[subject].selection_count if subject in preferences else 0,
            "last_selected_at": preferences[subject].last_selected_at if subject in preferences else None,
        }
        for subject in sorted_subjects
    ]


async def get_sorted_categories(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[str]:
    result = await db.execute(
        select(Category).where(Category.ledger_id == ledger_id).order_by(Category.display_order.asc())
    )
    categories = [category.name for category in result.scalars().all()]
    counts = await _get_counts(db, ledger_id, user_id, "category")
    return sort_tags_by_preference(categories, counts)


async def get_sorted_items(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
    category: str,
) -> list[str]:
    items = DEFAULT_ITEM_SUGGESTIONS.get(category, [])
    counts = await _get_counts(db, ledger_id, user_id, "item", category=category)
    custom_items = [item for item in counts if item not in items]
    return sort_tags_by_preference([*items, *custom_items], counts)


async def get_sorted_locations(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[str]:
    counts = await _get_counts(db, ledger_id, user_id, "location")
    return sorted(counts, key=lambda value: (-counts[value], value.casefold()))
