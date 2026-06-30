"""
偏好引擎响应 Schema
"""
from datetime import datetime
from typing import Literal
import uuid

from pydantic import BaseModel, Field


class PreferenceListResponse(BaseModel):
    items: list[str]


class PreferenceItemResponse(BaseModel):
    value: str
    selection_count: int
    last_selected_at: datetime | None = None


class PreferenceDetailListResponse(BaseModel):
    items: list[PreferenceItemResponse]


class TagChoiceResponse(BaseModel):
    id: uuid.UUID | None = None
    value: str
    is_system: bool
    selection_count: int = 0
    last_selected_at: datetime | None = None


class TagChoiceListResponse(BaseModel):
    items: list[TagChoiceResponse]


class CustomTagCreateRequest(BaseModel):
    tag_type: Literal["item", "location"]
    name: str = Field(..., min_length=1, max_length=100)
    category: str | None = Field(None, min_length=1, max_length=50)


class CustomTagUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class CustomTagResponse(BaseModel):
    id: uuid.UUID
    tag_type: str
    name: str
    category: str | None
    is_hidden: bool
