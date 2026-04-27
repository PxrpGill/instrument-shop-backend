"""
Tests for order schemas.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from apps.orders.models import OrderStatusChoices
from apps.orders.schemas import (
    OrderCreateSchema,
    OrderItemCreateSchema,
    OrderItemResponseSchema,
    OrderListResponseSchema,
    OrderResponseSchema,
    OrderStatusUpdateSchema,
)


class TestOrderItemCreateSchema:
    """Tests for OrderItemCreateSchema."""

    def test_valid_order_item(self):
        """Test valid order item schema."""
        schema = OrderItemCreateSchema(product_id=1, quantity=5)
        assert schema.product_id == 1
        assert schema.quantity == 5

    def test_default_quantity(self):
        """Test default quantity is 1."""
        schema = OrderItemCreateSchema(product_id=1)
        assert schema.quantity == 1

    def test_quantity_must_be_positive(self):
        """Test quantity must be at least 1."""
        with pytest.raises(ValidationError):
            OrderItemCreateSchema(product_id=1, quantity=0)

    def test_quantity_zero_fails(self):
        """Test quantity of 0 fails validation."""
        with pytest.raises(ValidationError):
            OrderItemCreateSchema(product_id=1, quantity=0)

    def test_quantity_negative_fails(self):
        """Test negative quantity fails validation."""
        with pytest.raises(ValidationError):
            OrderItemCreateSchema(product_id=1, quantity=-1)


class TestOrderCreateSchema:
    """Tests for OrderCreateSchema."""

    def test_valid_order_create(self):
        """Test valid order creation schema."""
        schema = OrderCreateSchema(
            contact_email="test@example.com",
            contact_phone="+1234567890",
            first_name="John",
            last_name="Doe",
            address="123 Main St",
            notes="Leave at door",
            items=[OrderItemCreateSchema(product_id=1, quantity=2)],
        )
        assert schema.contact_email == "test@example.com"
        assert schema.items[0].quantity == 2

    def test_email_validation_valid(self):
        """Test valid email passes validation."""
        schema = OrderCreateSchema(
            contact_email="valid@example.com",
            items=[OrderItemCreateSchema(product_id=1)],
        )
        assert schema.contact_email == "valid@example.com"

    def test_email_validation_invalid(self):
        """Test invalid email fails validation."""
        with pytest.raises(ValidationError):
            OrderCreateSchema(
                contact_email="not-an-email",
                items=[OrderItemCreateSchema(product_id=1)],
            )

    def test_email_validation_no_at_symbol(self):
        """Test email without @ fails validation."""
        with pytest.raises(ValidationError):
            OrderCreateSchema(
                contact_email="invalid-email.com",
                items=[OrderItemCreateSchema(product_id=1)],
            )

    def test_email_validation_empty_string(self):
        """Test empty email fails validation."""
        with pytest.raises(ValidationError):
            OrderCreateSchema(
                contact_email="",
                items=[OrderItemCreateSchema(product_id=1)],
            )

    def test_items_required(self):
        """Test items field is required."""
        with pytest.raises(ValidationError):
            OrderCreateSchema(contact_email="test@example.com")

    def test_items_cannot_be_empty(self):
        """Test empty items list fails validation."""
        with pytest.raises(ValidationError):
            OrderCreateSchema(
                contact_email="test@example.com",
                items=[],
            )

    def test_multiple_items_allowed(self):
        """Test multiple items in order."""
        schema = OrderCreateSchema(
            contact_email="test@example.com",
            items=[
                OrderItemCreateSchema(product_id=1, quantity=2),
                OrderItemCreateSchema(product_id=2, quantity=1),
                OrderItemCreateSchema(product_id=3, quantity=5),
            ],
        )
        assert len(schema.items) == 3

    def test_default_optional_fields(self):
        """Test optional fields have correct defaults."""
        schema = OrderCreateSchema(
            contact_email="test@example.com",
            items=[OrderItemCreateSchema(product_id=1)],
        )
        assert schema.contact_phone == ""
        assert schema.first_name == ""
        assert schema.last_name == ""
        assert schema.address == ""
        assert schema.notes == ""


class TestOrderItemResponseSchema:
    """Tests for OrderItemResponseSchema."""

    def test_from_attributes_decimal_serialization(self):
        """Test Decimal fields serialize to string."""

        # Create mock object simulating Django model
        class MockItem:
            id = 1
            product_id = 5
            product_name = "Test Product"
            quantity = 3
            unit_price = Decimal("99.99")
            subtotal = Decimal("299.97")

        schema = OrderItemResponseSchema.model_validate(MockItem())
        data = schema.model_dump()

        assert data["id"] == 1
        assert data["product_id"] == 5
        assert data["product_name"] == "Test Product"
        assert data["quantity"] == 3
        assert data["unit_price"] == "99.99"
        assert data["subtotal"] == "299.97"
        assert isinstance(data["unit_price"], str)
        assert isinstance(data["subtotal"], str)


class TestOrderResponseSchema:
    """Tests for OrderResponseSchema."""

    def test_status_serialization_to_string(self):
        """Test status enum serializes to string value."""
        from apps.orders.models import OrderStatusChoices

        class MockOrder:
            id = 1
            status = OrderStatusChoices.PROCESSING
            contact_email = "test@example.com"
            contact_phone = "+1234567890"
            first_name = "John"
            last_name = "Doe"
            address = "123 Main St"
            notes = "Test notes"
            total_amount = Decimal("199.99")
            created_at = datetime(2024, 1, 15, 10, 30, 0)
            updated_at = datetime(2024, 1, 15, 10, 30, 0)

            class items:
                @staticmethod
                def all():
                    return []

        schema = OrderResponseSchema.model_validate(MockOrder())
        data = schema.model_dump()

        # Status should be string, not enum
        assert data["status"] == "processing"
        assert isinstance(data["status"], str)

        # Decimal should be string
        assert data["total_amount"] == "199.99"
        assert isinstance(data["total_amount"], str)

        # Datetime should be string
        assert data["created_at"] == "2024-01-15T10:30:00"
        assert isinstance(data["created_at"], str)

    def test_items_from_related_manager(self):
        """Test items are converted from related manager to list."""

        class MockOrderItem:
            id = 1
            product_id = 5
            product_name = "Test Product"
            quantity = 2
            unit_price = Decimal("50.00")
            subtotal = Decimal("100.00")

        class MockItems:
            def all(self):
                return [MockOrderItem()]

        class MockOrder:
            id = 1
            status = OrderStatusChoices.NEW
            contact_email = "test@example.com"
            contact_phone = ""
            first_name = ""
            last_name = ""
            address = ""
            notes = ""
            total_amount = Decimal("100.00")
            created_at = datetime.now()
            updated_at = datetime.now()
            items = MockItems()

        schema = OrderResponseSchema.model_validate(MockOrder())
        data = schema.model_dump()

        assert len(data["items"]) == 1
        assert data["items"][0]["product_name"] == "Test Product"
        assert data["items"][0]["quantity"] == 2


class TestOrderListResponseSchema:
    """Tests for OrderListResponseSchema."""

    def test_items_count_from_related_manager(self):
        """Test items_count is calculated from related manager."""

        class MockItems:
            def count(self):
                return 5

        class MockOrder:
            id = 1
            status = OrderStatusChoices.CONFIRMED
            contact_email = "test@example.com"
            total_amount = Decimal("500.00")
            created_at = datetime.now()
            items = MockItems()

        schema = OrderListResponseSchema.model_validate(MockOrder())
        data = schema.model_dump()

        assert data["items_count"] == 5
        assert isinstance(data["items_count"], int)
        assert data["status"] == "confirmed"
        assert data["total_amount"] == "500.00"


class TestOrderStatusUpdateSchema:
    """Tests for OrderStatusUpdateSchema."""

    def test_valid_status_update(self):
        """Test valid status update schema."""
        schema = OrderStatusUpdateSchema(status=OrderStatusChoices.PROCESSING)
        assert schema.status == OrderStatusChoices.PROCESSING

    def test_allowed_statuses_valid(self):
        """
        Test that only allowed statuses are valid for update.

        BE-030: Only processing, confirmed, cancelled, completed are allowed.
        """
        allowed_statuses = [
            OrderStatusChoices.PROCESSING,
            OrderStatusChoices.CONFIRMED,
            OrderStatusChoices.CANCELLED,
            OrderStatusChoices.COMPLETED,
        ]
        for status_choice in allowed_statuses:
            schema = OrderStatusUpdateSchema(status=status_choice)
            assert schema.status == status_choice

    def test_new_status_rejected(self):
        """
        Test that 'new' status is rejected for update.

        BE-030: 'new' is not in the allowed set of statuses.
        """
        with pytest.raises(Exception):  # Pydantic ValidationError
            OrderStatusUpdateSchema(status=OrderStatusChoices.NEW)

    def test_invalid_status_fails(self):
        """Test invalid status value fails validation."""
        with pytest.raises(ValidationError):
            OrderStatusUpdateSchema(status="invalid_status")

    def test_status_as_string(self):
        """Test status can be passed as string."""
        schema = OrderStatusUpdateSchema(status="completed")
        assert schema.status == OrderStatusChoices.COMPLETED


class TestSchemaSerialization:
    """Tests for schema serialization correctness."""

    def test_full_order_serialization_types(self):
        """Test all fields have correct types after serialization."""
        from apps.orders.models import OrderStatusChoices

        class MockOrderItem:
            id = 1
            product_id = 5
            product_name = "Test Product"
            quantity = 2
            unit_price = Decimal("99.99")
            subtotal = Decimal("199.98")

        class MockItems:
            def all(self):
                return [MockOrderItem()]

        class MockOrder:
            id = 1
            status = OrderStatusChoices.NEW
            contact_email = "test@example.com"
            contact_phone = ""
            first_name = ""
            last_name = ""
            address = ""
            notes = ""
            total_amount = Decimal("199.98")
            created_at = datetime.now()
            updated_at = datetime.now()
            items = MockItems()

        schema = OrderResponseSchema.model_validate(MockOrder())
        data = schema.model_dump()

        # Verify types
        assert isinstance(data["id"], int)
        assert isinstance(data["status"], str)
        assert isinstance(data["contact_email"], str)
        assert isinstance(data["total_amount"], str)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)
        assert isinstance(data["items"], list)
        assert isinstance(data["items"][0]["unit_price"], str)
        assert isinstance(data["items"][0]["subtotal"], str)

    def test_order_list_serialization_types(self):
        """Test OrderListResponseSchema fields have correct types."""
        from apps.orders.models import OrderStatusChoices

        class MockItems:
            def count(self):
                return 3

        class MockOrder:
            id = 1
            status = OrderStatusChoices.PROCESSING
            contact_email = "test@example.com"
            total_amount = Decimal("299.99")
            created_at = datetime.now()
            items = MockItems()

        schema = OrderListResponseSchema.model_validate(MockOrder())
        data = schema.model_dump()

        assert isinstance(data["id"], int)
        assert isinstance(data["status"], str)
        assert isinstance(data["contact_email"], str)
        assert isinstance(data["total_amount"], str)
        assert isinstance(data["items_count"], int)
        assert isinstance(data["created_at"], str)
