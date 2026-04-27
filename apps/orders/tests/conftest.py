"""
Test fixtures for orders app.
"""

from decimal import Decimal

import pytest

from apps.orders.models import Order, OrderItem, OrderStatusChoices
from apps.products.models import Product


@pytest.fixture
def order_factory(customer_factory):
    """Fixture factory to create test orders."""

    def create_order(
        customer=None,
        status: str = OrderStatusChoices.NEW,
        contact_email: str = "test@example.com",
        contact_phone: str = "+1234567890",
        first_name: str = "John",
        last_name: str = "Doe",
        address: str = "123 Main St",
        notes: str = "",
        **kwargs
    ) -> Order:
        if customer is None:
            customer = customer_factory()
        return Order.objects.create(
            customer=customer,
            status=status,
            contact_email=contact_email,
            contact_phone=contact_phone,
            first_name=first_name,
            last_name=last_name,
            address=address,
            notes=notes,
            **kwargs
        )

    return create_order


@pytest.fixture
def order_item_factory(order_factory, product_factory):
    """Fixture factory to create test order items."""

    def create_order_item(
        order=None,
        product=None,
        product_name: str = None,
        quantity: int = 1,
        unit_price: Decimal = None,
        **kwargs
    ) -> OrderItem:
        if order is None:
            order = order_factory()
        if product is None:
            product = product_factory(price=unit_price or Decimal("99.99"))
        if product_name is None:
            product_name = product.name
        if unit_price is None:
            unit_price = product.price or Decimal("99.99")
        return OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            **kwargs
        )

    return create_order_item


@pytest.fixture
def published_product_factory(product_factory):
    """Fixture factory to create published products."""

    def create_published_product(
        name: str = "Published Product", price: float = 99.99, **kwargs
    ) -> Product:
        return product_factory(name=name, price=price, status="published", **kwargs)

    return create_published_product
