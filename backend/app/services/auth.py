"""
认证业务逻辑服务
- 密码 hash（bcrypt, rounds=12）
- JWT 生成与解码
- FastAPI 依赖项：get_current_user、get_current_admin
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User

# ---------------------------------------------------------------------------
# 密码 hash 配置（bcrypt, rounds=12）
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# ---------------------------------------------------------------------------
# OAuth2 scheme（用于从 Authorization: Bearer 头提取 token）
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

GENERIC_LOGIN_ERROR = "Invalid email or password"


# ---------------------------------------------------------------------------
# 密码工具
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """使用 bcrypt（rounds=12）对密码进行哈希"""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """验证明文密码与哈希值是否匹配"""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT 工具
# ---------------------------------------------------------------------------

def create_access_token(
    user_id: uuid.UUID,
    is_admin: bool,
    password_changed_at: Optional[datetime],
) -> str:
    """
    生成 JWT access token。

    payload 字段：
    - sub: str(user_id)
    - is_admin: bool
    - iat: 签发时间（unix timestamp）
    - exp: 过期时间（iat + 7天）
    - pwd_iat: 密码最后修改时间（unix timestamp），仅当 password_changed_at 不为 None 时包含
    """
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(days=settings.access_token_expire_days)

    payload: dict = {
        "sub": str(user_id),
        "is_admin": is_admin,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    if password_changed_at is not None:
        # 统一转换为 UTC 再取 timestamp
        if password_changed_at.tzinfo is None:
            password_changed_at = password_changed_at.replace(tzinfo=timezone.utc)
        payload["pwd_iat"] = int(password_changed_at.timestamp())

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """
    解码并验证 JWT。

    :raises HTTPException 401: 若 token 无效或已过期
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def is_token_stale_after_password_change(
    payload: dict,
    password_changed_at: Optional[datetime],
) -> bool:
    """Return True when a JWT was issued before the user's latest password change."""
    if password_changed_at is None:
        return False

    issued_at: Optional[int] = payload.get("iat")
    if issued_at is None:
        return False

    changed_at = password_changed_at
    if changed_at.tzinfo is None:
        changed_at = changed_at.replace(tzinfo=timezone.utc)
    changed_at_ts = int(changed_at.timestamp())

    token_password_issued_at: Optional[int] = payload.get("pwd_iat")
    if token_password_issued_at is not None:
        return token_password_issued_at < changed_at_ts

    return issued_at <= changed_at_ts


# ---------------------------------------------------------------------------
# FastAPI 依赖项
# ---------------------------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI 依赖项：从 JWT 中提取当前用户。

    步骤：
    1. 解码 token（失败抛出 401）
    2. 查询 User（不存在抛出 401）
    3. 检查 is_active（False 返回 403）
    4. 检查 password_changed_at vs pwd_iat（密码已更改且 token 在更改前签发，返回 401）
    """
    payload = decode_access_token(token)

    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: invalid subject format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    if is_token_stale_after_password_change(payload, user.password_changed_at):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalidated due to password change. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI 依赖项：要求当前用户为管理员。

    :raises HTTPException 403: 若用户不是管理员
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
