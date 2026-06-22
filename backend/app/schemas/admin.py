"""
管理员后台 Schema
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.suggestion import AdminSuggestionResponse, SuggestionStatusUpdateRequest


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    nickname: Optional[str] = None
    display_name: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserStatusUpdateRequest(BaseModel):
    is_active: bool


class AdminStatsResponse(BaseModel):
    total_users: int
    total_ledgers: int
    total_transactions: int


__all__ = [
    "AdminStatsResponse",
    "AdminSuggestionResponse",
    "AdminUserResponse",
    "SuggestionStatusUpdateRequest",
    "UserStatusUpdateRequest",
]
