"""
预算相关模型：Budget、BudgetCategory
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ledger import Ledger


class Budget(Base):
    """账本预算配置表（每个账本最多一条，与 ledger_id 唯一绑定）"""

    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ledgers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    monthly_total: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    annual_total: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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
        back_populates="budget",
    )
    categories: Mapped[List["BudgetCategory"]] = relationship(
        "BudgetCategory",
        back_populates="budget",
        cascade="all, delete-orphan",
    )


class BudgetCategory(Base):
    """预算分类细分表"""

    __tablename__ = "budget_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    budget_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("budgets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    # Relationships
    budget: Mapped["Budget"] = relationship(
        "Budget",
        back_populates="categories",
    )
