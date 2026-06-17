"""
偏好引擎响应 Schema
"""
from datetime import datetime

from pydantic import BaseModel


class PreferenceListResponse(BaseModel):
    items: list[str]


class PreferenceItemResponse(BaseModel):
    value: str
    selection_count: int
    last_selected_at: datetime | None = None


class PreferenceDetailListResponse(BaseModel):
    items: list[PreferenceItemResponse]
