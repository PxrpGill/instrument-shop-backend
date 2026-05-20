"""Pydantic-схемы под контракт contracts/auth/*.json.

Сохранены отдельно от schemas.py (где живут схемы ролей и старый
профиль), чтобы новый /api/auth/ не зависел от устаревших полей.
"""

from datetime import datetime
from typing import Optional

from ninja import Schema
from pydantic import EmailStr, Field


# ============================================================================
# Request schemas
# ============================================================================


class RegisterRequest(Schema):
    username: str = Field(..., min_length=2, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    password_confirmation: str = Field(..., min_length=8, max_length=128)


class LoginRequest(Schema):
    email: EmailStr
    password: str


class RefreshRequest(Schema):
    refresh_token: str


class LogoutRequest(Schema):
    refresh_token: Optional[str] = None


class ForgotPasswordRequest(Schema):
    email: EmailStr


class ResetPasswordRequest(Schema):
    token: str
    password: str = Field(..., min_length=8, max_length=128)
    password_confirmation: str = Field(..., min_length=8, max_length=128)


# ============================================================================
# Response schemas (точно под shape контрактов)
# ============================================================================


class UserSchema(Schema):
    """contract: /api/auth/me и user в register/login."""

    id: str
    username: str
    email: str
    created_at: datetime


class TokenPair(Schema):
    """Базовая часть ответа auth: access + refresh + meta."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class AuthResponse(TokenPair):
    """register/login: TokenPair + user."""

    user: UserSchema


class MessageResponse(Schema):
    message: str
