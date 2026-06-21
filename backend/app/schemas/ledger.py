"""
账本相关 Pydantic Schema
"""
import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.services.currency import validate_supported_currency


EntryMode = Literal["receipt", "item"]
SubjectStepMode = Literal["required", "optional", "disabled"]
NecessityStepMode = Literal["required", "optional", "disabled"]
ShareRole = Literal["read-write", "read-only"]
ShareStatus = Literal["pending", "approved", "rejected"]


class LedgerCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    entry_mode: EntryMode
    subject_enabled: bool = False
    subject_step_mode: SubjectStepMode = "required"
    necessity_step_mode: NecessityStepMode = "disabled"
    default_currency_code: str = Field("JPY", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    timezone: str = Field("Asia/Tokyo", min_length=1, max_length=50)
    budget_enabled: bool = False

    @field_validator("default_currency_code")
    @classmethod
    def default_currency_is_supported(cls, value: str) -> str:
        return validate_supported_currency(value) or value


class LedgerUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    subject_step_mode: Optional[SubjectStepMode] = None
    necessity_step_mode: Optional[NecessityStepMode] = None
    default_currency_code: Optional[str] = Field(None, min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")

    @field_validator("default_currency_code")
    @classmethod
    def default_currency_is_supported(cls, value: Optional[str]) -> Optional[str]:
        return validate_supported_currency(value)


class LedgerResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    entry_mode: str
    subject_enabled: bool
    subject_step_mode: str
    necessity_step_mode: str
    default_currency_code: str
    timezone: str
    budget_enabled: bool
    total_amounts: dict[str, int] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SubjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class SubjectResponse(BaseModel):
    id: uuid.UUID
    ledger_id: uuid.UUID
    name: str
    is_preset: bool
    display_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class CategoryUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class CategoryResponse(BaseModel):
    id: uuid.UUID
    ledger_id: uuid.UUID
    name: str
    is_system: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShareRequestCreateRequest(BaseModel):
    role: ShareRole = "read-write"


class ShareRequestResponse(BaseModel):
    id: uuid.UUID
    ledger_id: uuid.UUID
    requester_id: uuid.UUID
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    id: uuid.UUID
    ledger_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ShareCodeResponse(BaseModel):
    ledger_id: uuid.UUID
    share_code: str
