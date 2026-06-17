"""
预算相关 Pydantic Schema
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BudgetCategoryRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=50)
    amount: int = Field(..., strict=True, ge=0)


class BudgetUpsertRequest(BaseModel):
    monthly_total: int = Field(..., strict=True, gt=0)
    annual_total: Optional[int] = Field(None, strict=True, gt=0)
    categories: Optional[list[BudgetCategoryRequest]] = None


class BudgetCategoryResponse(BaseModel):
    id: uuid.UUID
    budget_id: uuid.UUID
    category: str
    amount: int

    model_config = {"from_attributes": True}


class BudgetProgressResponse(BaseModel):
    monthly_spent: int
    monthly_total: int
    percentage: float
    warning: Optional[str] = None
    category_spending: dict[str, int] = {}


class BudgetResponse(BaseModel):
    id: uuid.UUID
    ledger_id: uuid.UUID
    monthly_total: int
    annual_total: Optional[int]
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    categories: list[BudgetCategoryResponse] = []
    progress: BudgetProgressResponse

    model_config = {"from_attributes": True}

