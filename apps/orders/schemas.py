"""
Order schemas for API request/response validation.

These schemas are used for creating and reading orders via the API.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    PlainSerializer,
    model_validator,
)

from apps.orders.models import OrderStatusChoices


def _serialize_decimal(value: Decimal) -> str:
    """Serialize Decimal to string representation."""
    return str(value)


def _serialize_datetime(value: datetime) -> str:
    """Serialize datetime to ISO format string."""
    return value.isoformat()


DecimalField = Annotated[
    Decimal,
    PlainSerializer(lambda v: str(v), return_type=str),
]
"""Decimal field that serializes to string."""

DatetimeField = Annotated[
    datetime,
    PlainSerializer(lambda v: v.isoformat() if v else None, return_type=Optional[str]),
]
"""Datetime field that serializes to ISO string."""


def _serialize_order_status(value: OrderStatusChoices) -> str:
    """Serialize OrderStatusChoices to string value."""
    return value.value


OrderStatusField = Annotated[
    OrderStatusChoices,
    PlainSerializer(_serialize_order_status, return_type=str),
]
"""Order status field that serializes to string value."""


class OrderItemCreateSchema(BaseModel):
    """Schema for creating an order item."""

    product_id: int = Field(..., description="Product ID to order")
    quantity: int = Field(default=1, ge=1, description="Quantity to order")


class OrderItemResponseSchema(BaseModel):
    """Schema for order item in response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: DecimalField
    subtotal: DecimalField


class OrderCreateSchema(BaseModel):
    """Schema for creating an order."""

    contact_email: EmailStr = Field(..., description="Contact email for order")
    contact_phone: str = Field(default="", description="Contact phone")
    first_name: str = Field(
        default="", max_length=100, description="Recipient first name"
    )
    last_name: str = Field(
        default="", max_length=100, description="Recipient last name"
    )
    address: str = Field(default="", description="Delivery address")
    notes: str = Field(default="", description="Order notes")
    items: list[OrderItemCreateSchema] = Field(
        ...,
        min_length=1,
        description="List of order items (at least one required)",
    )


class OrderResponseSchema(BaseModel):
    """Schema for order response (customer view)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatusField
    contact_email: EmailStr
    contact_phone: str
    first_name: str
    last_name: str
    address: str
    notes: str
    total_amount: DecimalField
    items: list[OrderItemResponseSchema]
    created_at: DatetimeField
    updated_at: DatetimeField

    @model_validator(mode="before")
    @classmethod
    def convert_related_managers(cls, data):
        """Convert Django related managers to lists for serialization."""
        if hasattr(data, "__dict__"):
            # It's a Django model instance
            data_dict = {}
            for field_name in cls.model_fields.keys():
                value = getattr(data, field_name, None)
                # Handle related managers
                if hasattr(value, "all") and callable(value.all):
                    value = list(value.all())
                data_dict[field_name] = value
            return data_dict
        return data


class OrderListResponseSchema(BaseModel):
    """Schema for order list response (summary)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatusField
    contact_email: EmailStr
    total_amount: DecimalField
    items_count: int
    created_at: DatetimeField

    @model_validator(mode="before")
    @classmethod
    def convert_related_managers(cls, data):
        """Convert Django related managers to counts for list view."""
        if hasattr(data, "__dict__"):
            # It's a Django model instance
            data_dict = {"items_count": 0}  # Default value
            for field_name in cls.model_fields.keys():
                if field_name == "items_count":
                    # Count items from related manager
                    if hasattr(data, "items"):
                        data_dict["items_count"] = data.items.count()
                    continue
                value = getattr(data, field_name, None)
                data_dict[field_name] = value
            return data_dict
        return data


class OrderStatusUpdateSchema(BaseModel):
    """
    Schema for updating order status (staff only).

    BE-030: Limit the set of allowable statuses.
    Only processing, confirmed, cancelled, and completed are allowed.
    """

    status: OrderStatusChoices = Field(
        ...,
        description="New order status (processing, confirmed, cancelled, completed only)",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_status(cls, data):
        """
        Validate that only allowed statuses can be set.

        BE-030: Reject status values that are not in the allowed list.
        """
        if isinstance(data, dict) and "status" in data:
            allowed_statuses = {
                OrderStatusChoices.PROCESSING,
                OrderStatusChoices.CONFIRMED,
                OrderStatusChoices.CANCELLED,
                OrderStatusChoices.COMPLETED,
            }
            if data["status"] not in allowed_statuses:
                raise ValueError(
                    f"Invalid status. Allowed values: "
                    f"{', '.join(s.value for s in allowed_statuses)}"
                )
        return data
