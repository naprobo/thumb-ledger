"""
认证相关 Pydantic v2 Schema
"""
import uuid
from datetime import datetime

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    nickname: Optional[str] = Field(None, max_length=50)


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequestSchema(BaseModel):
    email: EmailStr = Field(..., max_length=255)


class PasswordResetConfirmSchema(BaseModel):
    token: str = Field(..., min_length=1, max_length=255)
    new_password: str = Field(..., min_length=8, max_length=128)


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=128)


class LanguagePreferenceRequest(BaseModel):
    preferred_language: Literal["zh-CN", "en", "ja"]


class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50)
    preferred_language: Optional[Literal["zh-CN", "en", "ja"]] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    nickname: Optional[str] = None
    display_name: str
    is_admin: bool
    preferred_language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    detail: str
    code: str
