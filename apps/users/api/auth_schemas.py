"""Pydantic-схемы под контракт contracts/auth/*.json.

Сохранены отдельно от schemas.py (где живут схемы ролей и старый
профиль), чтобы новый /api/auth/ не зависел от устаревших полей.
"""

from datetime import datetime
from typing import Optional

from ninja import Schema
from pydantic import ConfigDict, EmailStr, Field


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

    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "ivan_petrov",
        "email": "ivan@example.ru",
        "created_at": "2024-09-15T10:30:00Z",
    }})

    id: str
    username: str
    email: str
    created_at: datetime


class TokenPair(Schema):
    """Базовая часть ответа auth: access + refresh + meta."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAiLCJleHAiOjE3MDAwMDAwMDB9.abc123",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAiLCJ0eXBlIjoicmVmcmVzaCJ9.xyz789",
        "token_type": "bearer",
        "expires_in": 3600,
    }})

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class AuthResponse(TokenPair):
    """register/login: TokenPair + user."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAiLCJleHAiOjE3MDAwMDAwMDB9.abc123",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAiLCJ0eXBlIjoicmVmcmVzaCJ9.xyz789",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "username": "ivan_petrov",
            "email": "ivan@example.ru",
            "created_at": "2024-09-15T10:30:00Z",
        },
    }})

    user: UserSchema


class MessageResponse(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "message": "Письмо для сброса пароля отправлено на указанный email.",
    }})

    message: str
