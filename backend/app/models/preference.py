"""
用户偏好引擎模型：Preference
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ledger import Ledger
    from app.models.user import User


class Preference(Base):
    """
    用户偏好计数表
    tag_type: 'subject' | 'category' | 'item'
    category 字段在 tag_type='item' 时非空
    """

    __tablename__ = "preferences"
    __table_args__ = (
        UniqueConstraint(
            "ledger_id",
            "user_id",
            "tag_type",
            "tag_value",
            "category",
            name="uq_preference_ledger_user_tag",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ledgers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 'subject' | 'category' | 'item'
    tag_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    tag_value: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    # tag_type='item' 时非空
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    selection_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_selected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    ledger: Mapped["Ledger"] = relationship(
        "Ledger",
        back_populates="preferences",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="preferences",
    )


class CustomTag(Base):
    """账本内可重命名、可隐藏的消费名称和消费地点标签。"""

    __tablename__ = "custom_tags"
    __table_args__ = (
        UniqueConstraint(
            "ledger_id",
            "tag_type",
            "scope",
            "name",
            name="uq_custom_tag_ledger_type_scope_name",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ledgers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 'item' | 'location'
    tag_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # item 使用 category 名称作为作用域，location 使用空字符串
    scope: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
