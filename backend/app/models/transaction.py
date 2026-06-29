"""
交易相关模型：Transaction、TransactionItem、TransactionSubject、TransactionImage
"""
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, PrimaryKeyConstraint, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ledger import Category, Ledger, Subject
    from app.models.user import User
    from app.models.recurring import RecurringTransaction


class Transaction(Base):
    """交易记录表"""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ledgers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recorded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entry_mode_snapshot: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    # 金额：最小货币单位（整数），避免浮点精度问题
    amount: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    # 'essential' | 'non-essential'
    necessity: Mapped[str] = mapped_column(
        String(20),
        default="essential",
        nullable=False,
    )
    note: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    location_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    recurring_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("recurring_transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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
        back_populates="transactions",
    )
    recorder: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="transactions",
        foreign_keys=[recorded_by],
    )
    recurring_transaction: Mapped[Optional["RecurringTransaction"]] = relationship(
        "RecurringTransaction",
        back_populates="generated_transactions",
        foreign_keys=[recurring_transaction_id],
    )
    items: Mapped[List["TransactionItem"]] = relationship(
        "TransactionItem",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )
    transaction_subjects: Mapped[List["TransactionSubject"]] = relationship(
        "TransactionSubject",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )
    images: Mapped[List["TransactionImage"]] = relationship(
        "TransactionImage",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )


class TransactionItem(Base):
    """交易商品明细表（Entry_Mode=item 时使用）"""

    __tablename__ = "transaction_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category_name_snapshot: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    item_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    amount: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="items",
    )
    category: Mapped[Optional["Category"]] = relationship(
        "Category",
    )


class TransactionSubject(Base):
    """交易与花费对象多对多关联表"""

    __tablename__ = "transaction_subjects"
    __table_args__ = (
        PrimaryKeyConstraint("transaction_id", "subject_id"),
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="transaction_subjects",
    )
    subject: Mapped["Subject"] = relationship(
        "Subject",
        back_populates="transaction_subjects",
    )


class TransactionImage(Base):
    """交易图片附件表"""

    __tablename__ = "transaction_images"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    storage_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="images",
    )
