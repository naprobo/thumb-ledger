"""
偏好引擎 API 路由
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.preference import PreferenceDetailListResponse, PreferenceListResponse
from app.services.auth import get_current_user
from app.services.ledger import get_ledger_or_404, require_read_ledger
from app.services.preference import (
    get_sorted_categories,
    get_sorted_items,
    get_sorted_subjects,
    get_subject_preference_details,
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
