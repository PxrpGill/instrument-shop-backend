"""
Tests for order models.
"""

from decimal import Decimal

import pytest
from django.db.models.deletion import ProtectedError
from django.core.exceptions import ValidationError

from apps.orders.models import Order, OrderItem, OrderStatusChoices


@pytest.mark.django_db
class TestOrderModel:
    """Tests for Order model."""

    def test_create_order_with_defaults(self, customer_factory):
        """Test creating order with default values."""
        customer = customer_factory()
        order = Order.objects.create(
            customer=customer,
            contact_email="test@example.com",
        )

        assert order.status == OrderStatusChoices.NEW
        assert order.contact_email == "test@example.com"
        assert order.contact_phone == ""
        assert order.first_name == ""
        assert order.last_name == ""
        assert order.address == ""
        assert order.notes == ""
        assert order.customer == customer

    def test_order_str(self, order_factory):
        """Test order string representation."""
        order = order_factory()
        assert str(order) == f"Order {order.pk} - {order.status}"

    def test_order_get_full_name_with_names(self, order_factory):
        """Test get_full_name with first and last name."""
        order = order_factory(first_name="John", last_name="Doe")
        assert order.get_full_name() == "John Doe"

    def test_order_get_full_name_empty(self, order_factory):
        """Test get_full_name when names are empty."""
        order = order_factory(first_name="", last_name="")
        assert order.get_full_name() == ""

    def test_order_total_amount_no_items(self, order_factory):
        """Test total_amount returns 0 when no items."""
        order = order_factory()
        assert order.total_amount == Decimal("0.00")

    def test_order_total_amount_with_items(self, order_item_factory, order_factory):
        """Test total_amount calculates correctly with items."""
        order = order_factory()
        order_item_factory(order=order, quantity=2, unit_price=Decimal("100.00"))
        order_item_factory(order=order, quantity=1, unit_price=Decimal("50.00"))

        order.refresh_from_db()
        assert order.total_amount == Decimal("250.00")

    def test_order_customer_protect_on_delete(self, customer_factory, order_factory):
        """Test customer cannot be deleted when orders exist."""
        customer = customer_factory()
        order_factory(customer=customer)

        with pytest.raises(ProtectedError):
            customer.delete()

    def test_order_status_choices(self):
        """Test all status choices are defined."""
        expected_values = ["new", "processing", "confirmed", "cancelled", "completed"]
        expected_labels = ["New", "Processing", "Confirmed", "Cancelled", "Completed"]

        assert len(OrderStatusChoices.choices) == 5

        # Check values
        actual_values = [choice[0] for choice in OrderStatusChoices.choices]
        for expected in expected_values:
            assert expected in actual_values

        # Check labels
        actual_labels = [choice[1] for choice in OrderStatusChoices.choices]
        for expected in expected_labels:
            assert expected in actual_labels


@pytest.mark.django_db
class TestOrderItemModel:
    """Tests for OrderItem model."""

    def test_create_order_item(self, order_factory, product_factory):
        """Test creating order item."""
        order = order_factory()
        product = product_factory(name="Test Product", price=Decimal("99.99"))

        item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            quantity=2,
            unit_price=product.price,
        )

        assert item.order == order
        assert item.product == product
        assert item.product_name == "Test Product"
        assert item.quantity == 2
        assert item.unit_price == Decimal("99.99")

    def test_order_item_str(self, order_item_factory):
        """Test order item string representation."""
        item = order_item_factory(product_name="Test Product", quantity=3)
        assert str(item) == "Test Product x 3"

    def test_order_item_subtotal(self, order_item_factory):
        """Test order item subtotal calculation."""
        item = order_item_factory(quantity=3, unit_price=Decimal("25.50"))
        assert item.subtotal == Decimal("76.50")

    def test_order_item_subtotal_single_quantity(self, order_item_factory):
        """Test order item subtotal with single quantity."""
        item = order_item_factory(quantity=1, unit_price=Decimal("100.00"))
        assert item.subtotal == Decimal("100.00")

    def test_order_item_product_protect_on_delete(self, order_factory, product_factory):
        """Test product cannot be deleted when order items exist."""
        product = product_factory()
        order = order_factory()
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            quantity=1,
            unit_price=product.price,
        )

        with pytest.raises(ProtectedError):
            product.delete()

    def test_order_item_cascade_on_order_delete(
        self, order_item_factory, order_factory
    ):
        """Test order items are deleted when order is deleted."""
        order = order_factory()
        item = order_item_factory(order=order)
        item_id = item.id

        order.delete()

        assert not OrderItem.objects.filter(id=item_id).exists()

    def test_order_item_product_name_snapshot(self, order_factory, product_factory):
        """Test product name is stored as snapshot."""
        product = product_factory(name="Original Name")
        order = order_factory()

        item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            quantity=1,
            unit_price=product.price,
        )

        # Change product name
        product.name = "New Name"
        product.save()

        # Item should still have original name
        item.refresh_from_db()
        assert item.product_name == "Original Name"


@pytest.mark.django_db
class TestOrderStatuses:
    """Tests for order status workflow."""

    def test_default_status_is_new(self, customer_factory):
        """Test new orders default to NEW status."""
        customer = customer_factory(email="status_test@example.com")
        order = Order.objects.create(
            customer=customer,
            contact_email="test@example.com",
        )
        assert order.status == OrderStatusChoices.NEW

    def test_order_status_update(self, order_factory):
        """Test order status can be updated."""
        order = order_factory(status=OrderStatusChoices.NEW)
        order.status = OrderStatusChoices.PROCESSING
        order.save()

        order.refresh_from_db()
        assert order.status == OrderStatusChoices.PROCESSING

    def test_all_status_transitions_valid(self, customer_factory, order_factory):
        """Test all status values can be set."""
        customer = customer_factory()
        for status_value in [
            "new",
            "processing",
            "confirmed",
            "cancelled",
            "completed",
        ]:
            order = Order.objects.create(
                customer=customer,
                contact_email="test@example.com",
                status=status_value,
            )
            assert order.status == status_value

    def test_invalid_status_rejected_by_full_clean(self, order_factory):
        """Test invalid status values fail model validation."""
        order = order_factory(status=OrderStatusChoices.NEW)
        order.status = "invalid_status"

        with pytest.raises(ValidationError):
            order.full_clean()
