"""
通知相关 Pydantic Schema
"""
import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    status: str
    payload: Optional[dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime
    read_at: Optional[datetime]

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    unread_count: int
