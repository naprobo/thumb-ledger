"""
偏好引擎 API 路由
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.preference import (
    CustomTagCreateRequest,
    CustomTagResponse,
    CustomTagUpdateRequest,
    PreferenceDetailListResponse,
    PreferenceListResponse,
    TagChoiceListResponse,
)
from app.services.auth import get_current_user
from app.services.ledger import get_ledger_or_404, require_read_ledger, require_write_ledger
from app.services.preference import (
    create_or_restore_custom_tag,
    get_custom_tag_or_404,
    get_item_choices,
    get_location_choices,
    get_sorted_categories,
    get_sorted_items,
    get_sorted_locations,
    get_sorted_subjects,
    get_subject_preference_details,
    rename_custom_tag,
)

router = APIRouter(prefix="/ledgers/{ledger_id}/preferences", tags=["preferences"])


@router.get("/subjects", response_model=PreferenceListResponse)
async def subjects(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PreferenceListResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    return PreferenceListResponse(
        items=await get_sorted_subjects(db, ledger_id, current_user.id)
    )


@router.get("/subjects/details", response_model=PreferenceDetailListResponse)
async def subject_details(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PreferenceDetailListResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    return PreferenceDetailListResponse(
        items=await get_subject_preference_details(db, ledger_id, current_user.id)
    )


@router.get("/categories", response_model=PreferenceListResponse)
async def categories(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PreferenceListResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    return PreferenceListResponse(
        items=await get_sorted_categories(db, ledger_id, current_user.id)
    )


@router.get("/items", response_model=PreferenceListResponse)
async def items(
    ledger_id: uuid.UUID,
    category: str = Query(..., min_length=1, max_length=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PreferenceListResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    return PreferenceListResponse(
        items=await get_sorted_items(db, ledger_id, current_user.id, category)
    )


@router.get("/locations", response_model=PreferenceListResponse)
async def locations(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PreferenceListResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    return PreferenceListResponse(
        items=await get_sorted_locations(db, ledger_id, current_user.id)
    )


@router.get("/items/details", response_model=TagChoiceListResponse)
async def item_details(
    ledger_id: uuid.UUID,
    category: str = Query(..., min_length=1, max_length=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TagChoiceListResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    return TagChoiceListResponse(items=await get_item_choices(db, ledger_id, current_user.id, category))


@router.get("/locations/details", response_model=TagChoiceListResponse)
async def location_details(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TagChoiceListResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    return TagChoiceListResponse(items=await get_location_choices(db, ledger_id, current_user.id))


def _custom_tag_response(tag) -> CustomTagResponse:
    return CustomTagResponse(
        id=tag.id,
        tag_type=tag.tag_type,
        name=tag.name,
        category=tag.scope or None,
        is_hidden=tag.is_hidden,
    )


@router.post("/tags", response_model=CustomTagResponse)
async def create_custom_tag(
    ledger_id: uuid.UUID,
    payload: CustomTagCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CustomTagResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    tag = await create_or_restore_custom_tag(
        db,
        ledger_id,
        payload.tag_type,
        payload.name.strip(),
        payload.category,
    )
    return _custom_tag_response(tag)


@router.patch("/tags/{tag_id}", response_model=CustomTagResponse)
async def update_custom_tag(
    ledger_id: uuid.UUID,
    tag_id: uuid.UUID,
    payload: CustomTagUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CustomTagResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    tag = await get_custom_tag_or_404(db, ledger_id, tag_id)
    return _custom_tag_response(await rename_custom_tag(db, tag, payload.name.strip()))


@router.delete("/tags/{tag_id}")
async def hide_custom_tag(
    ledger_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    tag = await get_custom_tag_or_404(db, ledger_id, tag_id)
    tag.is_hidden = True
    await db.flush()
    return {"detail": "Custom tag hidden successfully."}
