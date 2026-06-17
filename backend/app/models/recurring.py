"""
定期交易模型：RecurringTransaction
"""
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ledger import Ledger
    from app.models.user import User
    from app.models.transaction import Transaction


class RecurringTransaction(Base):
    """定期交易模板表"""

    __tablename__ = "recurring_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ledgers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # 'daily' | 'weekly' | 'monthly' | 'yearly'
    interval: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    next_run_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    # JSONB：存储交易模板快照
    template_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
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
    ledger: Mapped["Ledger"] = relationship(
        "Ledger",
        back_populates="recurring_transactions",
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="recurring_transactions",
        foreign_keys=[created_by],
    )
    generated_transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="recurring_transaction",
        foreign_keys="Transaction.recurring_transaction_id",
    )
