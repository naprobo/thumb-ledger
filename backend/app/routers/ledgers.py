"""
账本管理 API 路由
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ledger import Category, HiddenSubject, Ledger, LedgerMember, ShareRequest, Subject
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.ledger import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
    LedgerCreateRequest,
    LedgerResponse,
    LedgerUpdateRequest,
    MemberResponse,
    MemberRoleUpdateRequest,
    ShareCodeResponse,
    ShareRequestCreateRequest,
    ShareRequestResponse,
    SubjectCreateRequest,
    SubjectResponse,
)
from app.services.audit import (
    LEDGER_SHARE_APPROVED,
    LEDGER_SHARE_REJECTED,
    LEDGER_SHARED_USER_REMOVED,
    write_audit_log,
)
from app.services.auth import get_current_user
from app.services.ledger import (
    add_default_categories,
    add_default_subjects,
    add_notification,
    can_add_custom_subject,
    can_modify_preset_subject,
    can_modify_system_category,
    create_ledger_member,
    decode_share_code,
    encode_share_code,
    ensure_shared_member_limit,
    ensure_user_can_create_ledger,
    get_ledger_or_404,
    get_membership,
    get_pending_share_request_or_404,
    require_owner,
    require_read_ledger,
    require_write_ledger,
)

router = APIRouter(prefix="/ledgers", tags=["ledgers"])


def _source_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _display_name(user: User | None) -> str | None:
    return user.display_name if user else None


def _share_request_response(share_request: ShareRequest, requester: User | None) -> ShareRequestResponse:
    return ShareRequestResponse(
        id=share_request.id,
        ledger_id=share_request.ledger_id,
        requester_id=share_request.requester_id,
        requester_email=requester.email if requester else None,
        requester_nickname=requester.nickname if requester else None,
        requester_display_name=_display_name(requester),
        role=share_request.role,
        status=share_request.status,
        created_at=share_request.created_at,
        updated_at=share_request.updated_at,
    )


def _member_response(member: LedgerMember, user: User | None) -> MemberResponse:
    return MemberResponse(
        id=member.id,
        ledger_id=member.ledger_id,
        user_id=member.user_id,
        email=user.email if user else None,
        nickname=user.nickname if user else None,
        display_name=_display_name(user),
        role=member.role,
        joined_at=member.joined_at,
    )


@router.post("", response_model=LedgerResponse, status_code=status.HTTP_201_CREATED)
async def create_ledger(
    payload: LedgerCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Ledger:
    await ensure_user_can_create_ledger(db, current_user.id)
    ledger = Ledger(owner_id=current_user.id, **payload.model_dump())
    add_default_subjects(ledger)
    add_default_categories(ledger)
    db.add(ledger)
    await db.flush()
    return ledger


@router.get("", response_model=list[LedgerResponse])
async def list_ledgers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LedgerResponse]:
    result = await db.execute(
        select(Ledger)
        .outerjoin(LedgerMember, LedgerMember.ledger_id == Ledger.id)
        .where((Ledger.owner_id == current_user.id) | (LedgerMember.user_id == current_user.id))
        .order_by(Ledger.created_at.desc())
    )
    ledgers = list(result.scalars().unique().all())
    totals = await _ledger_total_amounts(db, [ledger.id for ledger in ledgers])
    return [
        LedgerResponse.model_validate(ledger).model_copy(update={"total_amounts": totals.get(ledger.id, {})})
        for ledger in ledgers
    ]


@router.get("/{ledger_id}", response_model=LedgerResponse)
async def get_ledger(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LedgerResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    totals = await _ledger_total_amounts(db, [ledger.id])
    return LedgerResponse.model_validate(ledger).model_copy(update={"total_amounts": totals.get(ledger.id, {})})


async def _ledger_total_amounts(db: AsyncSession, ledger_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict[str, int]]:
    if not ledger_ids:
        return {}
    result = await db.execute(
        select(Transaction.ledger_id, Transaction.currency_code, func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.ledger_id.in_(ledger_ids))
        .group_by(Transaction.ledger_id, Transaction.currency_code)
    )
    totals: dict[uuid.UUID, dict[str, int]] = {ledger_id: {} for ledger_id in ledger_ids}
    for ledger_id, currency_code, amount in result.all():
        totals[ledger_id][currency_code] = int(amount)
    return totals


@router.patch("/{ledger_id}", response_model=LedgerResponse)
async def update_ledger(
    ledger_id: uuid.UUID,
    payload: LedgerUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LedgerResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ledger, field, value)
    await db.flush()
    await db.refresh(ledger)
    totals = await _ledger_total_amounts(db, [ledger.id])
    return LedgerResponse.model_validate(ledger).model_copy(update={"total_amounts": totals.get(ledger.id, {})})


@router.delete("/{ledger_id}")
async def delete_ledger(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    await db.delete(ledger)
    return {"detail": "Ledger deleted successfully."}


@router.get("/{ledger_id}/subjects", response_model=list[SubjectResponse])
async def list_subjects(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Subject]:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    hidden_subjects = select(HiddenSubject.subject_id).where(
        HiddenSubject.ledger_id == ledger_id,
        HiddenSubject.user_id == current_user.id,
    )
    result = await db.execute(
        select(Subject)
        .where(Subject.ledger_id == ledger_id, ~Subject.id.in_(hidden_subjects))
        .order_by(Subject.display_order.asc())
    )
    return list(result.scalars().all())


@router.post("/{ledger_id}/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    ledger_id: uuid.UUID,
    payload: SubjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Subject:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    count = await db.scalar(
        select(func.count()).select_from(Subject).where(Subject.ledger_id == ledger_id, Subject.is_preset.is_(False))
    )
    if count is None:
        count = 0
    if not can_add_custom_subject(count):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Maximum subject limit reached")
    max_order = await db.scalar(select(func.max(Subject.display_order)).where(Subject.ledger_id == ledger_id))
    subject = Subject(ledger_id=ledger_id, name=payload.name, is_preset=False, display_order=(max_order or 0) + 1)
    db.add(subject)
    await db.flush()
    return subject


@router.delete("/{ledger_id}/subjects/{subject_id}")
async def delete_subject(
    ledger_id: uuid.UUID,
    subject_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    subject = await db.scalar(select(Subject).where(Subject.id == subject_id, Subject.ledger_id == ledger_id))
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    if not can_modify_preset_subject(subject.is_preset):
        hidden = await db.scalar(
            select(HiddenSubject).where(
                HiddenSubject.ledger_id == ledger_id,
                HiddenSubject.user_id == current_user.id,
                HiddenSubject.subject_id == subject_id,
            )
        )
        if hidden is None:
            db.add(HiddenSubject(ledger_id=ledger_id, user_id=current_user.id, subject_id=subject_id))
            await db.flush()
        return {"detail": "Subject hidden successfully."}
    await db.delete(subject)
    await db.flush()
    return {"detail": "Subject deleted successfully."}


@router.get("/{ledger_id}/categories", response_model=list[CategoryResponse])
async def list_categories(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Category]:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    result = await db.execute(
        select(Category).where(Category.ledger_id == ledger_id).order_by(Category.display_order.asc())
    )
    return list(result.scalars().all())


@router.post("/{ledger_id}/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    ledger_id: uuid.UUID,
    payload: CategoryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Category:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    result = await db.execute(select(Category).where(Category.ledger_id == ledger_id))
    display_order = len(result.scalars().all())
    category = Category(
        ledger_id=ledger_id,
        name=payload.name,
        is_system=False,
        display_order=display_order,
    )
    db.add(category)
    await db.flush()
    return category


@router.patch("/{ledger_id}/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    ledger_id: uuid.UUID,
    category_id: uuid.UUID,
    payload: CategoryUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Category:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    category = await db.scalar(select(Category).where(Category.id == category_id, Category.ledger_id == ledger_id))
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if not can_modify_system_category(category.is_system):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System category cannot be renamed")
    category.name = payload.name
    await db.flush()
    return category


@router.delete("/{ledger_id}/categories/{category_id}")
async def delete_category(
    ledger_id: uuid.UUID,
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_write_ledger(db, ledger, current_user)
    category = await db.scalar(select(Category).where(Category.id == category_id, Category.ledger_id == ledger_id))
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if not can_modify_system_category(category.is_system):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System category cannot be deleted")
    await db.delete(category)
    return {"detail": "Category deleted successfully."}


@router.get("/{ledger_id}/share-code", response_model=ShareCodeResponse)
async def get_share_code(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareCodeResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    return ShareCodeResponse(ledger_id=ledger.id, share_code=encode_share_code(ledger.id))


@router.post("/{ledger_id}/share-requests", response_model=ShareRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_share_request(
    ledger_id: str,
    payload: ShareRequestCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareRequestResponse:
    try:
        resolved_ledger_id = decode_share_code(ledger_id) if len(ledger_id) == 32 else uuid.UUID(ledger_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ledger not found") from exc
    ledger = await get_ledger_or_404(db, resolved_ledger_id)
    if ledger.owner_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Owner cannot request access")
    if await get_membership(db, ledger.id, current_user.id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a ledger member")

    share_request = ShareRequest(
        ledger_id=ledger.id,
        requester_id=current_user.id,
        role=payload.role,
        status="pending",
    )
    db.add(share_request)
    await db.flush()
    await add_notification(
        db,
        ledger.owner_id,
        "LEDGER_SHARE_REQUESTED",
        {
            "ledger_id": str(ledger.id),
            "ledger_name": ledger.name,
            "requester_id": str(current_user.id),
            "requester_display_name": current_user.display_name,
        },
    )
    await add_notification(
        db,
        current_user.id,
        "LEDGER_SHARE_PENDING",
        {
            "ledger_id": str(ledger.id),
            "ledger_name": ledger.name,
            "role": payload.role,
        },
    )
    return _share_request_response(share_request, current_user)


@router.get("/{ledger_id}/share-requests", response_model=list[ShareRequestResponse])
async def list_share_requests(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ShareRequestResponse]:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    result = await db.execute(
        select(ShareRequest, User)
        .join(User, User.id == ShareRequest.requester_id)
        .where(ShareRequest.ledger_id == ledger_id)
        .order_by(ShareRequest.created_at.desc())
    )
    return [_share_request_response(share_request, requester) for share_request, requester in result.all()]


@router.post("/{ledger_id}/share-requests/{request_id}/approve", response_model=ShareRequestResponse)
async def approve_share_request(
    ledger_id: uuid.UUID,
    request_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareRequestResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    await ensure_shared_member_limit(db, ledger_id)
    share_request = await get_pending_share_request_or_404(db, ledger_id, request_id)
    if await get_membership(db, ledger_id, share_request.requester_id) is None:
        await create_ledger_member(db, ledger_id, share_request.requester_id, share_request.role)
    share_request.status = "approved"
    await add_notification(
        db,
        share_request.requester_id,
        "LEDGER_SHARE_APPROVED",
        {"ledger_id": str(ledger_id), "ledger_name": ledger.name, "owner_display_name": current_user.display_name},
    )
    await write_audit_log(db, LEDGER_SHARE_APPROVED, current_user.id, _source_ip(request), {"ledger_id": str(ledger_id)})
    await db.flush()
    await db.refresh(share_request)
    requester = await db.get(User, share_request.requester_id)
    return _share_request_response(share_request, requester)


@router.post("/{ledger_id}/share-requests/{request_id}/reject", response_model=ShareRequestResponse)
async def reject_share_request(
    ledger_id: uuid.UUID,
    request_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareRequestResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    share_request = await get_pending_share_request_or_404(db, ledger_id, request_id)
    share_request.status = "rejected"
    await add_notification(
        db,
        share_request.requester_id,
        "LEDGER_SHARE_REJECTED",
        {"ledger_id": str(ledger_id), "ledger_name": ledger.name, "owner_display_name": current_user.display_name},
    )
    await write_audit_log(db, LEDGER_SHARE_REJECTED, current_user.id, _source_ip(request), {"ledger_id": str(ledger_id)})
    await db.flush()
    await db.refresh(share_request)
    requester = await db.get(User, share_request.requester_id)
    return _share_request_response(share_request, requester)


@router.get("/{ledger_id}/members", response_model=list[MemberResponse])
async def list_members(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MemberResponse]:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    result = await db.execute(
        select(LedgerMember, User)
        .join(User, User.id == LedgerMember.user_id)
        .where(LedgerMember.ledger_id == ledger_id)
        .order_by(LedgerMember.joined_at.asc())
    )
    return [_member_response(member, user) for member, user in result.all()]


@router.patch("/{ledger_id}/members/{user_id}", response_model=MemberResponse)
async def update_member_role(
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: MemberRoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    member = await get_membership(db, ledger_id, user_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    member.role = payload.role
    await add_notification(
        db,
        user_id,
        "LEDGER_MEMBER_ROLE_CHANGED",
        {"ledger_id": str(ledger_id), "ledger_name": ledger.name, "role": payload.role},
    )
    await db.flush()
    member_user = await db.get(User, user_id)
    return _member_response(member, member_user)


@router.delete("/{ledger_id}/members/{user_id}")
async def remove_member(
    ledger_id: uuid.UUID,
    user_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    member = await get_membership(db, ledger_id, user_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    await add_notification(
        db,
        user_id,
        "LEDGER_SHARED_USER_REMOVED",
        {"ledger_id": str(ledger_id), "ledger_name": ledger.name},
    )
    await db.delete(member)
    await write_audit_log(db, LEDGER_SHARED_USER_REMOVED, current_user.id, _source_ip(request), {"ledger_id": str(ledger_id)})
    return {"detail": "Member removed successfully."}
