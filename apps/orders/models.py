from django.db import models

from apps.products.models import TimeStampedModel


class OrderStatusChoices(models.TextChoices):
    """Order status choices."""

    NEW = "new", "New"
    PROCESSING = "processing", "Processing"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class Order(TimeStampedModel):
    """
    Order model representing a customer's order.

    Contains order status, customer contact information,
    and links to order items.
    """

    # Owner/Customer relation
    customer = models.ForeignKey(
        "users.Customer",
        on_delete=models.PROTECT,
        related_name="orders",
        help_text="Customer who placed this order",
    )

    # Order status
    status = models.CharField(
        max_length=20,
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.NEW,
        help_text="Order status: new, processing, confirmed, cancelled, completed",
    )

    # Customer contact information
    contact_email = models.EmailField(
        help_text="Contact email for this order (may differ from customer email)"
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact phone for this order",
    )
    first_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Recipient first name",
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Recipient last name",
    )
    address = models.TextField(
        blank=True,
        help_text="Delivery address",
    )

    # Optional notes
    notes = models.TextField(
        blank=True,
        help_text="Order notes or special instructions",
    )

    class Meta:
        db_table = "orders"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Order {self.pk} - {self.status}"

    @property
    def total_amount(self) -> "decimal.Decimal":
        """Calculate total amount of all order items."""
        from decimal import Decimal

        total = Decimal("0.00")
        for item in self.items.all():
            total += item.subtotal
        return total

    def get_full_name(self) -> str:
        """Return recipient's full name."""
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return ""


class OrderItem(TimeStampedModel):
    """
    Order item model representing a product in an order.

    Stores a snapshot of product fields (name, price) at the time of order
    to preserve pricing even if product changes later.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Order this item belongs to",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
        help_text="Product ordered",
    )

    # Snapshot of product name at time of order
    product_name = models.CharField(
        max_length=255,
        help_text="Product name snapshot at time of order",
    )

    # Quantity and price
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Quantity ordered",
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Unit price snapshot at time of order",
    )

    class Meta:
        db_table = "order_items"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"

    @property
    def subtotal(self) -> "decimal.Decimal":
        """Calculate subtotal for this item (quantity * unit_price)."""
        from decimal import Decimal

        return Decimal(str(self.quantity)) * self.unit_price
