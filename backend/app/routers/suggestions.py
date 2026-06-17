"""
用户建议 API
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.suggestion import Suggestion, SuggestionVote
from app.models.user import User
from app.schemas.suggestion import SuggestionCreateRequest, SuggestionResponse, SuggestionVoteRequest
from app.services.auth import get_current_user

router = APIRouter(prefix="/suggestions", tags=["suggestions"])


async def _vote_counts(db: AsyncSession, suggestion_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict[str, int]]:
    if not suggestion_ids:
        return {}
    rows = await db.execute(
        select(SuggestionVote.suggestion_id, SuggestionVote.vote_type, func.count())
        .where(SuggestionVote.suggestion_id.in_(suggestion_ids))
        .group_by(SuggestionVote.suggestion_id, SuggestionVote.vote_type)
    )
    counts = {suggestion_id: {"support": 0, "oppose": 0} for suggestion_id in suggestion_ids}
    for suggestion_id, vote_type, count in rows.all():
        counts[suggestion_id][vote_type] = count
    return counts


async def _my_votes(
    db: AsyncSession,
    suggestion_ids: list[uuid.UUID],
    user_id: uuid.UUID,
) -> dict[uuid.UUID, str]:
    if not suggestion_ids:
        return {}
    rows = await db.execute(
        select(SuggestionVote.suggestion_id, SuggestionVote.vote_type).where(
            SuggestionVote.suggestion_id.in_(suggestion_ids),
            SuggestionVote.user_id == user_id,
        )
    )
    return dict(rows.all())


async def _responses(
    db: AsyncSession,
    suggestions: list[Suggestion],
    current_user: User,
) -> list[SuggestionResponse]:
    suggestion_ids = [suggestion.id for suggestion in suggestions]
    counts = await _vote_counts(db, suggestion_ids)
    my_votes = await _my_votes(db, suggestion_ids, current_user.id)
    return [
        SuggestionResponse(
            id=suggestion.id,
            author_id=suggestion.author_id,
            title=suggestion.title,
            body=suggestion.body,
            is_public=suggestion.is_public,
            status=suggestion.status,
            support_count=counts.get(suggestion.id, {}).get("support", 0),
            oppose_count=counts.get(suggestion.id, {}).get("oppose", 0),
            my_vote=my_votes.get(suggestion.id),
            created_at=suggestion.created_at,
            updated_at=suggestion.updated_at,
        )
        for suggestion in suggestions
    ]


@router.post("", response_model=SuggestionResponse, status_code=status.HTTP_201_CREATED)
async def create_suggestion(
    payload: SuggestionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuggestionResponse:
    suggestion = Suggestion(
        author_id=current_user.id,
        title=payload.title,
        body=payload.body,
        is_public=payload.is_public,
        status="new",
    )
    db.add(suggestion)
    await db.flush()
    return (await _responses(db, [suggestion], current_user))[0]


@router.get("/mine", response_model=list[SuggestionResponse])
async def my_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SuggestionResponse]:
    result = await db.execute(
        select(Suggestion).where(Suggestion.author_id == current_user.id).order_by(Suggestion.created_at.desc())
    )
    return await _responses(db, list(result.scalars().all()), current_user)


@router.get("/public", response_model=list[SuggestionResponse])
async def public_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SuggestionResponse]:
    result = await db.execute(
        select(Suggestion).where(Suggestion.is_public.is_(True)).order_by(Suggestion.created_at.desc())
    )
    return await _responses(db, list(result.scalars().all()), current_user)


@router.post("/{suggestion_id}/vote", response_model=SuggestionResponse)
async def vote_suggestion(
    suggestion_id: uuid.UUID,
    payload: SuggestionVoteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuggestionResponse:
    suggestion = await db.get(Suggestion, suggestion_id)
    if suggestion is None or not suggestion.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")
    if suggestion.author_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authors cannot vote on their own suggestion")

    result = await db.execute(
        select(SuggestionVote).where(
            SuggestionVote.suggestion_id == suggestion_id,
            SuggestionVote.user_id == current_user.id,
        )
    )
    vote = result.scalar_one_or_none()
    if vote is None:
        vote = SuggestionVote(suggestion_id=suggestion_id, user_id=current_user.id, vote_type=payload.vote_type)
        db.add(vote)
    else:
        vote.vote_type = payload.vote_type
    await db.flush()
    return (await _responses(db, [suggestion], current_user))[0]
