"""
用户建议相关 Schema
"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SuggestionStatus = Literal["new", "reviewing", "planned", "completed", "declined"]
SuggestionVoteType = Literal["support", "oppose"]


class SuggestionCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=2000)
    is_public: bool = False


class SuggestionVoteRequest(BaseModel):
    vote_type: SuggestionVoteType


class SuggestionStatusUpdateRequest(BaseModel):
    status: SuggestionStatus


class SuggestionResponse(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    title: str
    body: str
    is_public: bool
    status: SuggestionStatus
    support_count: int = 0
    oppose_count: int = 0
    my_vote: SuggestionVoteType | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminSuggestionResponse(SuggestionResponse):
    author_email: str
