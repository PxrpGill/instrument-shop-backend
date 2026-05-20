"""
Tests for order services.
"""
import pytest
from decimal import Decimal

from apps.orders.models import DeliveryTypeChoices, Order, OrderStatusChoices
from apps.orders.services import OrderCreationError, OrderService
from apps.orders.schemas import OrderCreateSchema, OrderItemCreateSchema
from apps.products.models import Product, ProductStatusChoices


@pytest.mark.django_db
class TestOrderServiceCreateOrder:
    """Tests for OrderService.create_order method."""

    def test_create_order_success(self, regular_customer, published_product_factory):
        """Test successful order creation."""
        product = published_product_factory(name="Test Product", price=100.00)
        
        order_data = OrderCreateSchema(
            contact_email="test@example.com",
            items=[OrderItemCreateSchema(product_id=product.id, quantity=2)]
        )
        
        order = OrderService.create_order(regular_customer, order_data)
        
        assert order is not None
        assert order.customer == regular_customer
        assert order.status == OrderStatusChoices.NEW
        assert order.items.count() == 1
        
        item = order.items.first()
        assert item.product == product
        assert item.quantity == 2
        assert item.unit_price == Decimal("100.00")

    def test_create_order_with_multiple_items(self, regular_customer, published_product_factory):
        """Test order creation with multiple items."""
        product1 = published_product_factory(name="Product 1", price=50.00)
        product2 = published_product_factory(name="Product 2", price=75.00)
        
        order_data = OrderCreateSchema(
            contact_email="test@example.com",
            items=[
                OrderItemCreateSchema(product_id=product1.id, quantity=1),
                OrderItemCreateSchema(product_id=product2.id, quantity=3),
            ]
        )
        
        order = OrderService.create_order(regular_customer, order_data)
        
        assert order.items.count() == 2

    def test_create_order_nonexistent_product(self, regular_customer):
        """Test order creation fails with nonexistent product."""
        order_data = OrderCreateSchema(
            contact_email="test@example.com",
            items=[OrderItemCreateSchema(product_id=99999, quantity=1)]
        )
        
        with pytest.raises(OrderCreationError) as exc_info:
            OrderService.create_order(regular_customer, order_data)
        
        assert "not found" in str(exc_info.value.errors).lower()

    def test_create_order_draft_product(self, regular_customer, product_factory):
        """Test order creation fails with draft product."""
        draft_product = product_factory(name="Draft", price=100.00, status="draft")
        
        order_data = OrderCreateSchema(
            contact_email="test@example.com",
            items=[OrderItemCreateSchema(product_id=draft_product.id, quantity=1)]
        )
        
        with pytest.raises(OrderCreationError) as exc_info:
            OrderService.create_order(regular_customer, order_data)
        
        assert "not available" in str(exc_info.value.errors).lower() or "published" in str(exc_info.value.errors).lower()

    def test_create_order_archived_product(self, regular_customer, product_factory):
        """Test order creation fails with archived product."""
        archived_product = product_factory(name="Archived", price=100.00, status="archived")
        
        order_data = OrderCreateSchema(
            contact_email="test@example.com",
            items=[OrderItemCreateSchema(product_id=archived_product.id, quantity=1)]
        )
        
        with pytest.raises(OrderCreationError) as exc_info:
            OrderService.create_order(regular_customer, order_data)
        
        assert "not available" in str(exc_info.value.errors).lower() or "published" in str(exc_info.value.errors).lower()

    def test_create_order_product_without_price(self, regular_customer, product_factory):
        """Test order creation fails with product without price."""
        product = product_factory(name="No Price", price=None, status="published")
        
        order_data = OrderCreateSchema(
            contact_email="test@example.com",
            items=[OrderItemCreateSchema(product_id=product.id, quantity=1)]
        )
        
        with pytest.raises(OrderCreationError) as exc_info:
            OrderService.create_order(regular_customer, order_data)
        
        assert "without price" in str(exc_info.value.errors).lower()

    def test_order_number_assigned_on_creation(self, regular_customer, published_product_factory):
        """Заказ получает уникальный номер вида NNNNN-X после создания."""
        product = published_product_factory(name="Hammer", price=100.00)

        order_data = OrderCreateSchema(
            contact_email="test@example.com",
            items=[OrderItemCreateSchema(product_id=product.id, quantity=1)],
        )
        order = OrderService.create_order(regular_customer, order_data)

        assert order.order_number is not None
        assert order.order_number.endswith("-1")
        # Глобальный счётчик равен id заказа, дополненному нулями до 5 символов
        assert order.order_number == f"{order.id:05d}-1"

    def test_order_number_increments_per_customer(
        self, regular_customer, published_product_factory
    ):
        """Второй заказ того же клиента получает суффикс -2, потом -3."""
        product = published_product_factory(name="Drill", price=200.00)

        order1 = OrderService.create_order(
            regular_customer,
            OrderCreateSchema(
                contact_email="a@example.com",
                items=[OrderItemCreateSchema(product_id=product.id, quantity=1)],
            ),
        )
        order2 = OrderService.create_order(
            regular_customer,
            OrderCreateSchema(
                contact_email="a@example.com",
                items=[OrderItemCreateSchema(product_id=product.id, quantity=1)],
            ),
        )
        order3 = OrderService.create_order(
            regular_customer,
            OrderCreateSchema(
                contact_email="a@example.com",
                items=[OrderItemCreateSchema(product_id=product.id, quantity=1)],
            ),
        )

        assert order1.order_number.endswith("-1")
        assert order2.order_number.endswith("-2")
        assert order3.order_number.endswith("-3")

    def test_order_number_per_customer_independent(
        self, regular_customer, customer_factory, published_product_factory
    ):
        """Счётчик заказов независим для каждого клиента."""
        other_customer = customer_factory(email="another@example.com")
        product = published_product_factory(name="Saw", price=50.00)

        order_a1 = OrderService.create_order(
            regular_customer,
            OrderCreateSchema(
                contact_email="a@example.com",
                items=[OrderItemCreateSchema(product_id=product.id, quantity=1)],
            ),
        )
        order_b1 = OrderService.create_order(
            other_customer,
            OrderCreateSchema(
                contact_email="b@example.com",
                items=[OrderItemCreateSchema(product_id=product.id, quantity=1)],
            ),
        )
        order_a2 = OrderService.create_order(
            regular_customer,
            OrderCreateSchema(
                contact_email="a@example.com",
                items=[OrderItemCreateSchema(product_id=product.id, quantity=1)],
            ),
        )

        assert order_a1.order_number.endswith("-1")
        assert order_b1.order_number.endswith("-1")  # независимо от первого клиента
        assert order_a2.order_number.endswith("-2")

    def test_create_pickup_order(self, regular_customer, published_product_factory):
        """Самовывоз — адрес и координаты не нужны."""
        product = published_product_factory(name="Wrench", price=75.00)

        order_data = OrderCreateSchema(
            contact_email="pickup@example.com",
            delivery_type=DeliveryTypeChoices.PICKUP,
            items=[OrderItemCreateSchema(product_id=product.id, quantity=1)],
        )
        order = OrderService.create_order(regular_customer, order_data)

        assert order.delivery_type == DeliveryTypeChoices.PICKUP
        assert order.address == ""
        assert order.latitude is None
        assert order.longitude is None

    def test_create_delivery_order_with_coords(
        self, regular_customer, published_product_factory
    ):
        """Доставка — адрес и координаты сохраняются."""
        product = published_product_factory(name="Bolt", price=10.00)

        order_data = OrderCreateSchema(
            contact_email="deliv@example.com",
            delivery_type=DeliveryTypeChoices.DELIVERY,
            address="ул. Ленина, 1",
            latitude=Decimal("55.751244"),
            longitude=Decimal("37.618423"),
            items=[OrderItemCreateSchema(product_id=product.id, quantity=2)],
        )
        order = OrderService.create_order(regular_customer, order_data)

        assert order.delivery_type == DeliveryTypeChoices.DELIVERY
        assert order.address == "ул. Ленина, 1"
        assert order.latitude == Decimal("55.751244")
        assert order.longitude == Decimal("37.618423")

    def test_delivery_without_address_rejected(self):
        """Доставка без адреса — ValidationError на уровне схемы."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc:
            OrderCreateSchema(
                contact_email="x@example.com",
                delivery_type=DeliveryTypeChoices.DELIVERY,
                latitude=Decimal("55.7"),
                longitude=Decimal("37.6"),
                items=[OrderItemCreateSchema(product_id=1, quantity=1)],
            )
        assert "Адрес" in str(exc.value)

    def test_delivery_without_coords_rejected(self):
        """Доставка без координат — ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc:
            OrderCreateSchema(
                contact_email="x@example.com",
                delivery_type=DeliveryTypeChoices.DELIVERY,
                address="ул. Ленина, 1",
                items=[OrderItemCreateSchema(product_id=1, quantity=1)],
            )
        assert "Координаты" in str(exc.value)

    def test_pickup_ignores_address_and_coords(self):
        """Pickup-заказ обнуляет адрес и координаты при сохранении."""
        schema = OrderCreateSchema(
            contact_email="x@example.com",
            delivery_type=DeliveryTypeChoices.PICKUP,
            address="должно быть отброшено",
            latitude=Decimal("55.7"),
            longitude=Decimal("37.6"),
            items=[OrderItemCreateSchema(product_id=1, quantity=1)],
        )
        assert schema.address == ""
        assert schema.latitude is None
        assert schema.longitude is None

    def test_price_snapshot_at_creation(self, regular_customer, published_product_factory):
        """Test that product price is snapshotted at creation."""
        product = published_product_factory(name="Guitar", price=299.99)
        
        order_data = OrderCreateSchema(
            contact_email="test@example.com",
            items=[OrderItemCreateSchema(product_id=product.id, quantity=1)]
        )
        
        order = OrderService.create_order(regular_customer, order_data)
        item = order.items.first()
        
        assert item.unit_price == Decimal("299.99")
        
        # Change product price after order
        product.price = Decimal("999.99")
        product.save()
        
        # Refresh from db to verify snapshot
        item.refresh_from_db()
        assert item.unit_price == Decimal("299.99")


@pytest.mark.django_db
class TestOrderServiceGetOrderTotal:
    """Tests for OrderService.get_order_total method."""

    def test_get_order_total_with_items(self, order_factory, order_item_factory):
        """Test getting total amount for order with items."""
        order = order_factory()
        order_item_factory(order=order, unit_price=Decimal("100.00"), quantity=2)
        order_item_factory(order=order, unit_price=Decimal("50.00"), quantity=1)
        
        total = OrderService.get_order_total(order)
        
        assert total == Decimal("250.00")

    def test_get_order_total_no_items(self, order_factory):
        """Test getting total amount for order without items."""
        order = order_factory()
        
        total = OrderService.get_order_total(order)
        
        assert total == Decimal("0.00")


@pytest.mark.django_db
class TestOrderServiceCanCancelOrder:
    """Tests for OrderService.can_cancel_order method."""

    def test_can_cancel_new_order(self, order_factory):
        """Test that NEW order can be cancelled."""
        order = order_factory(status=OrderStatusChoices.NEW)
        
        result = OrderService.can_cancel_order(order)
        
        assert result is True

    def test_can_cancel_processing_order(self, order_factory):
        """Test that PROCESSING order can be cancelled."""
        order = order_factory(status=OrderStatusChoices.PROCESSING)
        
        result = OrderService.can_cancel_order(order)
        
        assert result is True

    def test_cannot_cancel_confirmed_order(self, order_factory):
        """Test that CONFIRMED order cannot be cancelled."""
        order = order_factory(status=OrderStatusChoices.CONFIRMED)
        
        result = OrderService.can_cancel_order(order)
        
        assert result is False

    def test_cannot_cancel_completed_order(self, order_factory):
        """Test that COMPLETED order cannot be cancelled."""
        order = order_factory(status=OrderStatusChoices.COMPLETED)
        
        result = OrderService.can_cancel_order(order)
        
        assert result is False

    def test_cannot_cancel_already_cancelled_order(self, order_factory):
        """Test that already CANCELLED order cannot be cancelled again."""
        order = order_factory(status=OrderStatusChoices.CANCELLED)
        
        result = OrderService.can_cancel_order(order)
        
        assert result is False
