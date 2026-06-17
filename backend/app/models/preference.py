"""
用户偏好引擎模型：Preference
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
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
