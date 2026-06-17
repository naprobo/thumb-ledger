"""
管理员后台 API
"""
import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ledger import Ledger
from app.models.suggestion import Suggestion, SuggestionVote
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.admin import (
    AdminStatsResponse,
    AdminSuggestionResponse,
    AdminUserResponse,
    SuggestionStatusUpdateRequest,
    UserStatusUpdateRequest,
)
from app.services.audit import ADMIN_ACTION, write_audit_log
from app.services.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


def _source_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    _current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


@router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
async def update_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdateRequest,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await db.get(User, user_id)
    if user is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = payload.is_active
    await write_audit_log(
        db,
        ADMIN_ACTION,
        current_admin.id,
        _source_ip(request),
        {"action": "update_user_status", "target_user_id": str(user_id), "is_active": payload.is_active},
    )
    await db.flush()
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    user = await db.get(User, user_id)
    if user is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await write_audit_log(
        db,
        ADMIN_ACTION,
        current_admin.id,
        _source_ip(request),
        {"action": "delete_user", "target_user_id": str(user_id)},
    )
    await db.delete(user)
    return {"detail": "User deleted successfully."}


@router.get("/stats", response_model=AdminStatsResponse)
async def stats(
    _current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminStatsResponse:
    total_users = await db.scalar(select(func.count()).select_from(User))
    total_ledgers = await db.scalar(select(func.count()).select_from(Ledger))
    total_transactions = await db.scalar(select(func.count()).select_from(Transaction))
    return AdminStatsResponse(
        total_users=total_users or 0,
        total_ledgers=total_ledgers or 0,
        total_transactions=total_transactions or 0,
    )


async def _admin_suggestion_response(db: AsyncSession, suggestion: Suggestion) -> AdminSuggestionResponse:
    support_count = await db.scalar(
        select(func.count()).select_from(SuggestionVote).where(
            SuggestionVote.suggestion_id == suggestion.id,
            SuggestionVote.vote_type == "support",
        )
    )
    oppose_count = await db.scalar(
        select(func.count()).select_from(SuggestionVote).where(
            SuggestionVote.suggestion_id == suggestion.id,
            SuggestionVote.vote_type == "oppose",
        )
    )
    author = await db.get(User, suggestion.author_id)
    return AdminSuggestionResponse(
        id=suggestion.id,
        author_id=suggestion.author_id,
        author_email=author.email if author else "-",
        title=suggestion.title,
        body=suggestion.body,
        is_public=suggestion.is_public,
        status=suggestion.status,
        support_count=support_count or 0,
        oppose_count=oppose_count or 0,
        my_vote=None,
        created_at=suggestion.created_at,
        updated_at=suggestion.updated_at,
    )


@router.get("/suggestions", response_model=list[AdminSuggestionResponse])
async def list_suggestions(
    _current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminSuggestionResponse]:
    result = await db.execute(select(Suggestion).order_by(Suggestion.created_at.desc()))
    suggestions = list(result.scalars().all())
    return [await _admin_suggestion_response(db, suggestion) for suggestion in suggestions]


@router.patch("/suggestions/{suggestion_id}/status", response_model=AdminSuggestionResponse)
async def update_suggestion_status(
    suggestion_id: uuid.UUID,
    payload: SuggestionStatusUpdateRequest,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminSuggestionResponse:
    suggestion = await db.get(Suggestion, suggestion_id)
    if suggestion is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")
    suggestion.status = payload.status
    await write_audit_log(
        db,
        ADMIN_ACTION,
        current_admin.id,
        _source_ip(request),
        {"action": "update_suggestion_status", "suggestion_id": str(suggestion_id), "status": payload.status},
    )
    await db.flush()
    await db.refresh(suggestion)
    return await _admin_suggestion_response(db, suggestion)
