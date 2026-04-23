from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Dict, List, Any
from datetime import datetime
from apps.users.models import CustomerRole


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
    roles: List[str] = Field(default_factory=list)
    permissions: Dict[str, bool] = Field(default_factory=dict)
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


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


# ============================================================================
# Role Schemas
# ============================================================================

class RoleSchema(BaseModel):
    """Schema for Role output."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    permissions: Dict[str, bool]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RoleCreateSchema(BaseModel):
    """Schema for Role creation."""
    name: str = Field(..., min_length=3, max_length=50, pattern="^[a-z_]+$")
    description: Optional[str] = Field(None, max_length=500)
    permissions: Dict[str, bool]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "manager",
                "description": "Менеджер - управление товарами",
                "permissions": {
                    "create_product": True,
                    "edit_product": True,
                    "delete_product": True,
                    "view_category": True
                }
            }
        }
    )


class RoleUpdateSchema(BaseModel):
    """Schema for Role update."""
    description: Optional[str] = Field(None, max_length=500)
    permissions: Dict[str, bool]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Обновленное описание",
                "permissions": {
                    "create_product": True,
                    "edit_product": True
                }
            }
        }
    )


class RoleAssignmentSchema(BaseModel):
    """Schema for assigning a role to a customer."""
    role_name: str = Field(..., min_length=3, max_length=50)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role_name": "manager"
            }
        }
    )


class CustomerRoleListSchema(BaseModel):
    """Schema for CustomerRole output (list of user's roles)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: str
    role_id: int
    role_name: str
    assigned_at: datetime
    assigned_by_email: Optional[str] = None

    @classmethod
    def from_model(cls, customer_role: CustomerRole):
        """Create schema from CustomerRole model."""
        return cls(
            id=customer_role.id,
            customer_id=str(customer_role.customer.id),
            role_id=customer_role.role.id,
            role_name=customer_role.role.name,
            assigned_at=customer_role.assigned_at,
            assigned_by_email=customer_role.assigned_by.email if customer_role.assigned_by else None
        )


class BulkRoleAssignmentSchema(BaseModel):
    """Schema for bulk role assignment."""
    customer_ids: List[str]
    role_name: str = Field(..., min_length=3, max_length=50)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_ids": ["uuid-1", "uuid-2"],
                "role_name": "manager"
            }
        }
    )
