"""
账本管理 API 路由
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ledger import Category, HiddenSubject, Ledger, LedgerMember, ShareRequest, Subject
from app.models.user import User
from app.schemas.ledger import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
    LedgerCreateRequest,
    LedgerResponse,
    LedgerUpdateRequest,
    MemberResponse,
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
) -> list[Ledger]:
    result = await db.execute(
        select(Ledger)
        .outerjoin(LedgerMember, LedgerMember.ledger_id == Ledger.id)
        .where((Ledger.owner_id == current_user.id) | (LedgerMember.user_id == current_user.id))
        .order_by(Ledger.created_at.desc())
    )
    return list(result.scalars().unique().all())


@router.get("/{ledger_id}", response_model=LedgerResponse)
async def get_ledger(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Ledger:
    ledger = await get_ledger_or_404(db, ledger_id)
    await require_read_ledger(db, ledger, current_user)
    return ledger


@router.patch("/{ledger_id}", response_model=LedgerResponse)
async def update_ledger(
    ledger_id: uuid.UUID,
    payload: LedgerUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Ledger:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ledger, field, value)
    await db.flush()
    await db.refresh(ledger)
    return ledger


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
) -> ShareRequest:
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
        {"ledger_id": str(ledger.id), "requester_id": str(current_user.id)},
    )
    return share_request


@router.get("/{ledger_id}/share-requests", response_model=list[ShareRequestResponse])
async def list_share_requests(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ShareRequest]:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    result = await db.execute(
        select(ShareRequest).where(ShareRequest.ledger_id == ledger_id).order_by(ShareRequest.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/{ledger_id}/share-requests/{request_id}/approve", response_model=ShareRequestResponse)
async def approve_share_request(
    ledger_id: uuid.UUID,
    request_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareRequest:
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
        {"ledger_id": str(ledger_id)},
    )
    await write_audit_log(db, LEDGER_SHARE_APPROVED, current_user.id, _source_ip(request), {"ledger_id": str(ledger_id)})
    await db.flush()
    await db.refresh(share_request)
    return share_request


@router.post("/{ledger_id}/share-requests/{request_id}/reject", response_model=ShareRequestResponse)
async def reject_share_request(
    ledger_id: uuid.UUID,
    request_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareRequest:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    share_request = await get_pending_share_request_or_404(db, ledger_id, request_id)
    share_request.status = "rejected"
    await add_notification(
        db,
        share_request.requester_id,
        "LEDGER_SHARE_REJECTED",
        {"ledger_id": str(ledger_id)},
    )
    await write_audit_log(db, LEDGER_SHARE_REJECTED, current_user.id, _source_ip(request), {"ledger_id": str(ledger_id)})
    await db.flush()
    await db.refresh(share_request)
    return share_request


@router.get("/{ledger_id}/members", response_model=list[MemberResponse])
async def list_members(
    ledger_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LedgerMember]:
    ledger = await get_ledger_or_404(db, ledger_id)
    require_owner(ledger, current_user)
    result = await db.execute(
        select(LedgerMember).where(LedgerMember.ledger_id == ledger_id).order_by(LedgerMember.joined_at.asc())
    )
    return list(result.scalars().all())


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
        {"ledger_id": str(ledger_id)},
    )
    await db.delete(member)
    await write_audit_log(db, LEDGER_SHARED_USER_REMOVED, current_user.id, _source_ip(request), {"ledger_id": str(ledger_id)})
    return {"detail": "Member removed successfully."}
