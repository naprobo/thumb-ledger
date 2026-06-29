"""
交易相关 Pydantic Schema
"""
import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.services.currency import validate_supported_currency

Necessity = Literal["essential", "non-essential"]
TimeRange = Literal["week", "month", "year", "custom"]


class TransactionItemRequest(BaseModel):
    category_id: Optional[uuid.UUID] = None
    category_name: Optional[str] = Field(None, min_length=1, max_length=50)
    item_name: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: int = Field(..., strict=True, gt=0)
    currency_code: Optional[str] = Field(None, min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")

    @field_validator("currency_code")
    @classmethod
    def currency_is_supported(cls, value: Optional[str]) -> Optional[str]:
        return validate_supported_currency(value)


class TransactionCreateRequest(BaseModel):
    amount: int = Field(..., strict=True, gt=0)
    currency_code: Optional[str] = Field(None, min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    transaction_date: Optional[date] = None
    necessity: Necessity = "essential"
    note: Optional[str] = Field(None, max_length=500)
    items: list[TransactionItemRequest] = Field(default_factory=list, max_length=100)
    subject_ids: list[uuid.UUID] = Field(default_factory=list, max_length=20)

    @field_validator("currency_code")
    @classmethod
    def currency_is_supported(cls, value: Optional[str]) -> Optional[str]:
        return validate_supported_currency(value)

    @field_validator("items")
    @classmethod
    def item_count_is_reasonable(cls, value: list[TransactionItemRequest]) -> list[TransactionItemRequest]:
        if len(value) > 100:
            raise ValueError("too many transaction items")
        return value


class TransactionUpdateRequest(BaseModel):
    amount: Optional[int] = Field(None, strict=True, gt=0)
    currency_code: Optional[str] = Field(None, min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    transaction_date: Optional[date] = None
    necessity: Optional[Necessity] = None
    note: Optional[str] = Field(None, max_length=500)
    items: Optional[list[TransactionItemRequest]] = Field(None, max_length=100)
    subject_ids: Optional[list[uuid.UUID]] = Field(None, max_length=20)

    @field_validator("currency_code")
    @classmethod
    def currency_is_supported(cls, value: Optional[str]) -> Optional[str]:
        return validate_supported_currency(value)


class TransactionItemResponse(BaseModel):
    id: uuid.UUID
    category_id: Optional[uuid.UUID]
    category_name_snapshot: str
    item_name: Optional[str]
    amount: int
    currency_code: str

    model_config = {"from_attributes": True}


class TransactionSubjectResponse(BaseModel):
    subject_id: uuid.UUID

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    id: uuid.UUID
    ledger_id: uuid.UUID
    recorded_by: Optional[uuid.UUID]
    entry_mode_snapshot: Optional[str]
    amount: int
    currency_code: str
    transaction_date: date
    necessity: str
    note: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: list[TransactionItemResponse] = []
    transaction_subjects: list[TransactionSubjectResponse] = []
    budget_warning: Optional[str] = None

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    page: int
    page_size: int
    total: int
    page_total_amounts: dict[str, int]


class SummaryGroup(BaseModel):
    key: str
    currency_code: str
    amount: int


class LedgerSummaryResponse(BaseModel):
    categories: list[SummaryGroup]
    subjects: list[SummaryGroup]
    necessities: list[SummaryGroup]
