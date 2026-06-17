"""
认证 API 路由
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import PasswordResetToken, User
from app.schemas.auth import (
    DeleteAccountRequest,
    LanguagePreferenceRequest,
    LoginRequest,
    PasswordResetConfirmSchema,
    PasswordResetRequestSchema,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.audit import (
    ACCOUNT_DELETED,
    LOGIN_FAILED,
    LOGIN_SUCCESS,
    PASSWORD_RESET_CONFIRM,
    PASSWORD_RESET_REQUEST,
    REGISTER,
    write_audit_log,
)
from app.services.auth import (
    GENERIC_LOGIN_ERROR,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.services.email import send_password_reset_email
from app.services.rate_limit import (
    login_failed_limiter,
    password_reset_limiter,
    register_limiter,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

PASSWORD_RESET_RESPONSE = {
    "detail": "If the email exists, a password reset token has been sent."
}


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _source_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _rate_limit_key(prefix: str, value: str | None) -> str:
    return f"{prefix}:{value or 'unknown'}"


def _raise_rate_limited(retry_after: int) -> None:
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many requests",
        headers={"Retry-After": str(retry_after)},
    )


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: Request,
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> User:
    register_key = _rate_limit_key("register", _source_ip(request))
    rate_limit = register_limiter.hit(register_key)
    if not rate_limit.allowed:
        _raise_rate_limited(rate_limit.retry_after)

    email = _normalize_email(payload.email)
    existing = await db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    await db.flush()
    await write_audit_log(db, REGISTER, user.id, _source_ip(request), {"email": email})
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    login_key = _rate_limit_key("login_failed", _source_ip(request))
    rate_limit = login_failed_limiter.check(login_key)
    if not rate_limit.allowed:
        _raise_rate_limited(rate_limit.retry_after)

    email = _normalize_email(payload.email)
    user = await db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        rate_limit = login_failed_limiter.hit(login_key)
        if not rate_limit.allowed:
            _raise_rate_limited(rate_limit.retry_after)
        await write_audit_log(db, LOGIN_FAILED, None, _source_ip(request), {"email": email})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=GENERIC_LOGIN_ERROR,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    login_failed_limiter.clear(login_key)
    access_token = create_access_token(user.id, user.is_admin, user.password_changed_at)
    await write_audit_log(db, LOGIN_SUCCESS, user.id, _source_ip(request), None)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me/preferences", response_model=UserResponse)
async def update_my_preferences(
    payload: LanguagePreferenceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    current_user.preferred_language = payload.preferred_language
    await db.flush()
    return current_user


@router.post("/password-reset/request")
async def request_password_reset(
    request: Request,
    payload: PasswordResetRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    email = _normalize_email(payload.email)
    reset_key = _rate_limit_key("password_reset", email)
    rate_limit = password_reset_limiter.hit(reset_key)
    if not rate_limit.allowed:
        _raise_rate_limited(rate_limit.retry_after)

    user = await db.scalar(select(User).where(User.email == email))
    if user is None:
        await write_audit_log(
            db,
            PASSWORD_RESET_REQUEST,
            None,
            _source_ip(request),
            {"email": email, "matched": False},
        )
        return PASSWORD_RESET_RESPONSE

    settings = get_settings()
    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_reset_token(token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.password_reset_token_expire_minutes),
    )
    db.add(reset_token)
    await write_audit_log(
        db,
        PASSWORD_RESET_REQUEST,
        user.id,
        _source_ip(request),
        {"email": email, "matched": True},
    )

    try:
        await send_password_reset_email(email, token)
    except Exception:
        logger.exception("Password reset email failed for %s", email)

    return PASSWORD_RESET_RESPONSE


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: Request,
    payload: PasswordResetConfirmSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    token_hash = hash_reset_token(payload.token)
    reset_token = await db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    now = datetime.now(timezone.utc)
    if reset_token is None or reset_token.used or _as_aware_utc(reset_token.expires_at) < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    user = await db.scalar(select(User).where(User.id == reset_token.user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    user.password_hash = hash_password(payload.new_password)
    user.password_changed_at = now
    reset_token.used = True
    await write_audit_log(db, PASSWORD_RESET_CONFIRM, user.id, _source_ip(request), None)
    return {"detail": "Password has been reset successfully."}


@router.delete("/account")
async def delete_account(
    request: Request,
    payload: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=GENERIC_LOGIN_ERROR,
        )

    deleted_user_id = str(current_user.id)
    await db.execute(delete(AuditLog).where(AuditLog.user_id == current_user.id))
    await write_audit_log(
        db,
        ACCOUNT_DELETED,
        None,
        _source_ip(request),
        {"deleted_user_id": deleted_user_id},
    )
    await db.flush()
    await db.execute(delete(User).where(User.id == current_user.id))
    return {"detail": "Account deleted successfully."}
