"""
审计日志写入服务
"""
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

# 事件类型常量
LOGIN_SUCCESS = "LOGIN_SUCCESS"
LOGIN_FAILED = "LOGIN_FAILED"
REGISTER = "REGISTER"
PASSWORD_RESET_REQUEST = "PASSWORD_RESET_REQUEST"
PASSWORD_RESET_CONFIRM = "PASSWORD_RESET_CONFIRM"
ACCOUNT_DELETED = "ACCOUNT_DELETED"
LEDGER_SHARE_APPROVED = "LEDGER_SHARE_APPROVED"
LEDGER_SHARE_REJECTED = "LEDGER_SHARE_REJECTED"
LEDGER_SHARED_USER_REMOVED = "LEDGER_SHARED_USER_REMOVED"
ADMIN_ACTION = "ADMIN_ACTION"


async def write_audit_log(
    db: AsyncSession,
    event_type: str,
    user_id: Optional[uuid.UUID],
    source_ip: Optional[str],
    metadata: Optional[dict] = None,
) -> None:
    """
    写入审计日志记录。

    :param db: AsyncSession 数据库会话
    :param event_type: 事件类型（使用上方常量）
    :param user_id: 关联用户 ID（可为 None，如未认证的登录失败）
    :param source_ip: 请求来源 IP
    :param metadata: 额外元数据（JSON）
    """
    log = AuditLog(
        event_type=event_type,
        user_id=user_id,
        source_ip=source_ip,
        extra_data=metadata,
    )
    db.add(log)
    # 注意：不在此处 commit，由调用方的 session 统一提交
    await db.flush()
