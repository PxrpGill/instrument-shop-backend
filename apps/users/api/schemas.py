from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class CustomerRegisterRequest(BaseModel):
    """Схема для регистрации нового клиента."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class CustomerLoginRequest(BaseModel):
    """Схема для входа клиента."""
    email: EmailStr
    password: str


class CustomerProfileResponse(BaseModel):
    """Схема для отображения профиля клиента."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    email: str
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class CustomerUpdateRequest(BaseModel):
    """Схема для обновления профиля клиента."""
    phone: Optional[str] = Field(None, max_length=20)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None


class TokenResponse(BaseModel):
    """Схема для ответа с токенами."""
    access: str
    refresh: str
    token_type: str = "Bearer"


class TokenRefreshRequest(BaseModel):
    """Схема для обновления токена."""
    refresh: str


class ChangePasswordRequest(BaseModel):
    """Схема для смены пароля."""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)