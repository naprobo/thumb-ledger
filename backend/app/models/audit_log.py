"""
审计日志模型：AuditLog
仅追加（INSERT-only），不提供 UPDATE/DELETE 路径
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    """
    审计日志表
    - 不设 updated_at
    - 应用层不暴露 UPDATE/DELETE 接口
    - occurred_at 使用数据库服务端默认值
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    # IPv4 或 IPv6 地址（最长 45 字符）
    source_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    # 额外元数据（JSON）
    # 注意：使用 extra_data 作为 Python 属性名，数据库列名仍为 metadata
    # （因为 SQLAlchemy DeclarativeBase 保留了 'metadata' 属性名）
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
    )
