"""
用户相关模型：User、PasswordResetToken
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ledger import Ledger, LedgerMember, ShareRequest
    from app.models.audit_log import AuditLog
    from app.models.notification import Notification
    from app.models.preference import Preference
    from app.models.suggestion import Suggestion, SuggestionVote
    from app.models.transaction import Transaction
    from app.models.recurring import RecurringTransaction


class User(Base):
    """用户账户表"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    preferred_language: Mapped[str] = mapped_column(
        String(10),
        default="zh-CN",
        nullable=False,
    )
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    owned_ledgers: Mapped[List["Ledger"]] = relationship(
        "Ledger",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="Ledger.owner_id",
    )
    ledger_memberships: Mapped[List["LedgerMember"]] = relationship(
        "LedgerMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    share_requests: Mapped[List["ShareRequest"]] = relationship(
        "ShareRequest",
        back_populates="requester",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="recorder",
        foreign_keys="Transaction.recorded_by",
    )
    recurring_transactions: Mapped[List["RecurringTransaction"]] = relationship(
        "RecurringTransaction",
        back_populates="creator",
        foreign_keys="RecurringTransaction.created_by",
    )
    preferences: Mapped[List["Preference"]] = relationship(
        "Preference",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    password_reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    suggestions: Mapped[List["Suggestion"]] = relationship(
        "Suggestion",
        back_populates="author",
        cascade="all, delete-orphan",
    )
    suggestion_votes: Mapped[List["SuggestionVote"]] = relationship(
        "SuggestionVote",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class PasswordResetToken(Base):
    """密码重置令牌表"""

    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="password_reset_tokens",
    )
