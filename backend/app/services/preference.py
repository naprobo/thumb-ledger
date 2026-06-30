"""
偏好引擎服务。
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ledger import Category, HiddenSubject, Subject
from app.models.preference import CustomTag, Preference
from app.models.transaction import Transaction, TransactionItem
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
    return Subject.ledger_id == ledger_id, Subject.is_hidden.is_(False)


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
        select(Category)
        .where(Category.ledger_id == ledger_id, Category.is_hidden.is_(False))
        .order_by(Category.display_order.asc())
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
    return [row["value"] for row in await get_item_choices(db, ledger_id, user_id, category)]


async def get_sorted_locations(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[str]:
    return [row["value"] for row in await get_location_choices(db, ledger_id, user_id)]


async def _materialize_custom_tags(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    tag_type: str,
    scope: str,
    names: list[str],
) -> list[CustomTag]:
    result = await db.execute(
        select(CustomTag).where(
            CustomTag.ledger_id == ledger_id,
            CustomTag.tag_type == tag_type,
            CustomTag.scope == scope,
        )
    )
    existing = {tag.name: tag for tag in result.scalars().all()}
    for name in names:
        if name in existing:
            continue
        tag = CustomTag(ledger_id=ledger_id, tag_type=tag_type, scope=scope, name=name)
        db.add(tag)
        existing[name] = tag
    await db.flush()
    return list(existing.values())


async def get_item_choices(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
    category: str,
) -> list[dict]:
    defaults = DEFAULT_ITEM_SUGGESTIONS.get(category, [])
    preferences = await _get_preferences(db, ledger_id, user_id, "item", category=category)
    custom_names = [name for name in preferences if name not in defaults]
    custom_tags = await _materialize_custom_tags(db, ledger_id, "item", category, custom_names)
    visible_custom = [tag for tag in custom_tags if not tag.is_hidden]
    rows = [
        {
            "id": None,
            "value": name,
            "is_system": True,
            "selection_count": preferences[name].selection_count if name in preferences else 0,
            "last_selected_at": preferences[name].last_selected_at if name in preferences else None,
        }
        for name in defaults
    ]
    rows.extend(
        {
            "id": tag.id,
            "value": tag.name,
            "is_system": False,
            "selection_count": preferences[tag.name].selection_count if tag.name in preferences else 0,
            "last_selected_at": preferences[tag.name].last_selected_at if tag.name in preferences else None,
        }
        for tag in visible_custom
    )
    order = {name: index for index, name in enumerate(defaults)}
    return sorted(
        rows,
        key=lambda row: (
            -row["selection_count"],
            order.get(row["value"], len(defaults)),
            row["value"].casefold(),
        ),
    )


async def get_location_choices(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[dict]:
    preferences = await _get_preferences(db, ledger_id, user_id, "location")
    tags = await _materialize_custom_tags(db, ledger_id, "location", "", list(preferences))
    rows = [
        {
            "id": tag.id,
            "value": tag.name,
            "is_system": False,
            "selection_count": preferences[tag.name].selection_count if tag.name in preferences else 0,
            "last_selected_at": preferences[tag.name].last_selected_at if tag.name in preferences else None,
        }
        for tag in tags
        if not tag.is_hidden
    ]
    return sorted(rows, key=lambda row: (-row["selection_count"], row["value"].casefold()))


async def create_or_restore_custom_tag(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    tag_type: str,
    name: str,
    category: str | None,
) -> CustomTag:
    scope = category or ""
    if tag_type == "item" and not category:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Item tag requires category")
    existing = await db.scalar(
        select(CustomTag).where(
            CustomTag.ledger_id == ledger_id,
            CustomTag.tag_type == tag_type,
            CustomTag.scope == scope,
            func.lower(CustomTag.name) == name.casefold(),
        )
    )
    if existing is not None:
        existing.is_hidden = False
        await db.flush()
        return existing
    tag = CustomTag(ledger_id=ledger_id, tag_type=tag_type, scope=scope, name=name, is_hidden=False)
    db.add(tag)
    await db.flush()
    return tag


async def get_custom_tag_or_404(
    db: AsyncSession,
    ledger_id: uuid.UUID,
    tag_id: uuid.UUID,
) -> CustomTag:
    tag = await db.scalar(
        select(CustomTag).where(CustomTag.id == tag_id, CustomTag.ledger_id == ledger_id)
    )
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom tag not found")
    return tag


async def rename_custom_tag(
    db: AsyncSession,
    tag: CustomTag,
    new_name: str,
) -> CustomTag:
    duplicate = await db.scalar(
        select(CustomTag).where(
            CustomTag.ledger_id == tag.ledger_id,
            CustomTag.tag_type == tag.tag_type,
            CustomTag.scope == tag.scope,
            CustomTag.id != tag.id,
            func.lower(CustomTag.name) == new_name.casefold(),
        )
    )
    if duplicate is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag name already exists")

    old_name = tag.name
    if tag.tag_type == "location":
        await db.execute(
            update(Transaction)
            .where(
                Transaction.ledger_id == tag.ledger_id,
                (Transaction.location_tag_id == tag.id)
                | ((Transaction.location_tag_id.is_(None)) & (Transaction.location_name == old_name)),
            )
            .values(location_tag_id=tag.id, location_name=new_name)
        )
    else:
        transaction_ids = select(Transaction.id).where(Transaction.ledger_id == tag.ledger_id)
        await db.execute(
            update(TransactionItem)
            .where(
                TransactionItem.transaction_id.in_(transaction_ids),
                TransactionItem.category_name_snapshot == tag.scope,
                (TransactionItem.item_tag_id == tag.id)
                | ((TransactionItem.item_tag_id.is_(None)) & (TransactionItem.item_name == old_name)),
            )
            .values(item_tag_id=tag.id, item_name=new_name)
        )
    await db.execute(
        update(Preference)
        .where(
            Preference.ledger_id == tag.ledger_id,
            Preference.tag_type == tag.tag_type,
            Preference.tag_value == old_name,
            Preference.category == (tag.scope or None),
        )
        .values(tag_value=new_name)
    )
    tag.name = new_name
    await db.flush()
    return tag
