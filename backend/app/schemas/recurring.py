"""
定期交易 Schema
"""
import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.transaction import TransactionCreateRequest


RecurringInterval = Literal["daily", "weekly", "monthly", "yearly"]


class RecurringTemplateData(TransactionCreateRequest):
    transaction_date: None = None


class RecurringCreateRequest(BaseModel):
    interval: RecurringInterval
    next_run_date: date
    template_data: RecurringTemplateData


class RecurringUpdateRequest(BaseModel):
    interval: Optional[RecurringInterval] = None
    next_run_date: Optional[date] = None
    is_active: Optional[bool] = None
    template_data: Optional[RecurringTemplateData] = None


class RecurringResponse(BaseModel):
    id: uuid.UUID
    ledger_id: uuid.UUID
    created_by: Optional[uuid.UUID]
    interval: str
    next_run_date: date
    is_active: bool
    template_data: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

