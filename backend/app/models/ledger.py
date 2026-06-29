"""
账本相关模型：Ledger、LedgerMember、ShareRequest、Subject、Category
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transaction import Transaction
    from app.models.recurring import RecurringTransaction
    from app.models.budget import Budget
    from app.models.preference import Preference


class Ledger(Base):
    """账本表"""

    __tablename__ = "ledgers"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    # 'receipt' | 'item'
    entry_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    receipt_item_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    # 'required' | 'optional' | 'disabled'
    location_step_mode: Mapped[str] = mapped_column(
        String(20),
        default="optional",
        nullable=False,
    )
    subject_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    # 'required' | 'optional' | 'disabled'
    subject_step_mode: Mapped[str] = mapped_column(
        String(20),
        default="required",
        nullable=False,
    )
    # 'enabled' | 'disabled'
    necessity_step_mode: Mapped[str] = mapped_column(
        String(20),
        default="disabled",
        nullable=False,
    )
    default_currency_code: Mapped[str] = mapped_column(
        String(3),
        default="JPY",
        nullable=False,
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="Asia/Tokyo",
        nullable=False,
    )
    budget_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_ledgers",
        foreign_keys=[owner_id],
    )
    members: Mapped[List["LedgerMember"]] = relationship(
        "LedgerMember",
        back_populates="ledger",
        cascade="all, delete-orphan",
    )
    share_requests: Mapped[List["ShareRequest"]] = relationship(
        "ShareRequest",
        back_populates="ledger",
        cascade="all, delete-orphan",
    )
    subjects: Mapped[List["Subject"]] = relationship(
        "Subject",
        back_populates="ledger",
        cascade="all, delete-orphan",
    )
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="ledger",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="ledger",
        cascade="all, delete-orphan",
    )
    recurring_transactions: Mapped[List["RecurringTransaction"]] = relationship(
        "RecurringTransaction",
        back_populates="ledger",
        cascade="all, delete-orphan",
    )
    budget: Mapped[Optional["Budget"]] = relationship(
        "Budget",
        back_populates="ledger",
        cascade="all, delete-orphan",
        uselist=False,
    )
    preferences: Mapped[List["Preference"]] = relationship(
        "Preference",
        back_populates="ledger",
        cascade="all, delete-orphan",
    )
    hidden_subjects: Mapped[List["HiddenSubject"]] = relationship(
        "HiddenSubject",
        back_populates="ledger",
        cascade="all, delete-orphan",
    )


class LedgerMember(Base):
    """账本成员表（共享用户）"""

    __tablename__ = "ledger_members"

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
    # 'read-write' | 'read-only'
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    joined_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    ledger: Mapped["Ledger"] = relationship(
        "Ledger",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="ledger_memberships",
    )


class ShareRequest(Base):
    """账本共享申请表"""

    __tablename__ = "share_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ledgers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 'read-write' | 'read-only'
    role: Mapped[str] = mapped_column(
        String(20),
        default="read-write",
        nullable=False,
    )
    # 'pending' | 'approved' | 'rejected'
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
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
    ledger: Mapped["Ledger"] = relationship(
        "Ledger",
        back_populates="share_requests",
    )
    requester: Mapped["User"] = relationship(
        "User",
        back_populates="share_requests",
    )


class Subject(Base):
    """花费对象（Subject）表"""

    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ledgers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    is_preset: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    ledger: Mapped["Ledger"] = relationship(
        "Ledger",
        back_populates="subjects",
    )
    transaction_subjects: Mapped[List["TransactionSubject"]] = relationship(
        "TransactionSubject",
        back_populates="subject",
        cascade="all, delete-orphan",
    )
    hidden_by_users: Mapped[List["HiddenSubject"]] = relationship(
        "HiddenSubject",
        back_populates="subject",
        cascade="all, delete-orphan",
    )


class HiddenSubject(Base):
    """当前用户在某账本中隐藏的预设花费对象。"""

    __tablename__ = "hidden_subjects"

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
    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    ledger: Mapped["Ledger"] = relationship(
        "Ledger",
        back_populates="hidden_subjects",
    )
    subject: Mapped["Subject"] = relationship(
        "Subject",
        back_populates="hidden_by_users",
    )


# Import here to avoid circular imports
from app.models.transaction import TransactionSubject  # noqa: E402


class Category(Base):
    """账本分类表（系统默认分类 + 自定义分类）"""

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ledgers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
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

    ledger: Mapped["Ledger"] = relationship(
        "Ledger",
        back_populates="categories",
    )
