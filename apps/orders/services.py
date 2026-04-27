"""
Order services - business logic layer for order operations.

This module contains service functions for creating and managing orders.
All business logic for orders should be placed here, keeping controllers thin.
"""

from decimal import Decimal
from typing import Optional

from django.db import transaction

from apps.orders.models import Order, OrderItem, OrderStatusChoices
from apps.orders.schemas import OrderCreateSchema, OrderItemCreateSchema
from apps.products.models import Product, ProductStatusChoices
from apps.users.models import Customer


class OrderCreationError(Exception):
    """Exception raised when order creation fails due to validation errors."""

    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


class OrderService:
    """
    Service class for order-related business logic.

    Handles order creation with proper validation, transaction management,
    and price snapshotting.
    """

    @classmethod
    def create_order(
        cls,
        customer: Customer,
        order_data: OrderCreateSchema,
    ) -> Order:
        """
        Create a new order with items in a transaction.

        Args:
            customer: The customer placing the order
            order_data: Validated order creation schema with contact info and items

        Returns:
            The created Order instance with items

        Raises:
            OrderCreationError: If validation fails (e.g., product not published)
        """
        # Create order in transaction
        with transaction.atomic():
            # Validate all products inside the transaction to prevent race conditions
            product_ids = [item.product_id for item in order_data.items]
            products = cls._validate_and_get_products(product_ids)

            # Validate order items quantities
            cls._validate_order_items(order_data.items, products)

            # Create the order
            order = Order.objects.create(
                customer=customer,
                status=OrderStatusChoices.NEW,
                contact_email=order_data.contact_email,
                contact_phone=order_data.contact_phone,
                first_name=order_data.first_name,
                last_name=order_data.last_name,
                address=order_data.address,
                notes=order_data.notes,
            )

            # Create order items with price snapshots
            order_items = []
            for item_data in order_data.items:
                product = products[item_data.product_id]
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    quantity=item_data.quantity,
                    unit_price=product.price,  # Snapshot current price
                )
                order_items.append(order_item)

            # Refresh to load relations
            order.refresh_from_db()

            return order

    @classmethod
    def _validate_and_get_products(cls, product_ids: list[int]) -> dict[int, Product]:
        """
        Validate that all products exist and are published.

        Uses select_for_update() to lock rows and prevent race conditions.
        Must be called inside a transaction.atomic() block.

        Args:
            product_ids: List of product IDs to validate

        Returns:
            Dict mapping product_id to Product instance

        Raises:
            OrderCreationError: If any product is not found or not published
        """
        # Get unique product IDs
        unique_ids = list(set(product_ids))

        # Fetch products WITH ROW-LEVEL LOCK to prevent race conditions
        # This ensures no other transaction can modify these products
        # between validation and order item creation
        products = list(Product.objects.select_for_update().filter(pk__in=unique_ids))

        # Check all products were found
        found_ids = {p.id for p in products}
        missing_ids = set(unique_ids) - found_ids
        if missing_ids:
            raise OrderCreationError(
                {"products": f"Products not found: {sorted(missing_ids)}"}
            )

        # Check all products are published
        non_published = [
            p for p in products if p.status != ProductStatusChoices.PUBLISHED
        ]
        if non_published:
            non_published_ids = [p.id for p in non_published]
            non_published_names = [p.name for p in non_published]
            raise OrderCreationError(
                {
                    "products": f"Products are not available for order (must be published): "
                    f"{', '.join(non_published_names)} (IDs: {non_published_ids})"
                }
            )

        # Check all products have prices
        no_price = [p for p in products if p.price is None]
        if no_price:
            raise OrderCreationError(
                {
                    "products": f"Products without price: "
                    f"{', '.join(p.name for p in no_price)}"
                }
            )

        return {p.id: p for p in products}

    @classmethod
    def _validate_order_items(
        cls,
        items: list[OrderItemCreateSchema],
        products: dict[int, Product],
    ) -> None:
        """
        Validate order items (quantities, etc.).

        Args:
            items: List of order item schemas
            products: Dict mapping product_id to Product

        Raises:
            OrderCreationError: If validation fails
        """
        for item in items:
            if item.quantity < 1:
                raise OrderCreationError(
                    {
                        "quantity": f"Quantity must be at least 1 for product {item.product_id}"
                    }
                )

    @classmethod
    def get_order_total(cls, order: Order) -> Decimal:
        """
        Calculate total amount for an order.

        Args:
            order: The order to calculate total for

        Returns:
            Total amount as Decimal
        """
        return order.total_amount

    @classmethod
    def can_cancel_order(cls, order: Order) -> bool:
        """
        Check if an order can be cancelled.

        Orders can be cancelled if they are in NEW or PROCESSING status.

        Args:
            order: The order to check

        Returns:
            True if order can be cancelled, False otherwise
        """
        return order.status in (OrderStatusChoices.NEW, OrderStatusChoices.PROCESSING)
