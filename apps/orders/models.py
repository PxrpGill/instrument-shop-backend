from django.db import models

from apps.shared.models import TimeStampedModel


class OrderStatusChoices(models.TextChoices):
    """Статусы заказа."""

    NEW = "new", "Новый"
    PROCESSING = "processing", "В обработке"
    CONFIRMED = "confirmed", "Подтвержден"
    CANCELLED = "cancelled", "Отменен"
    COMPLETED = "completed", "Выполнен"


class DeliveryTypeChoices(models.TextChoices):
    """Способ получения заказа."""

    PICKUP = "pickup", "Самовывоз"
    DELIVERY = "delivery", "Доставка"


class Order(TimeStampedModel):
    """
    Order model representing a customer's order.

    Contains order status, customer contact information,
    and links to order items.
    """

    # Уникальный номер заказа в формате NNNNN-X,
    # где NNNNN — глобальный счётчик с ведущими нулями (по id заказа),
    # X — порядковый номер заказа этого клиента.
    # Заполняется в OrderService при создании; nullable, чтобы не блокировать
    # фабрики и существующие данные.
    order_number = models.CharField(
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        help_text="Уникальный номер заказа в формате NNNNN-X",
    )

    # Owner/Customer relation
    customer = models.ForeignKey(
        "users.Customer",
        on_delete=models.PROTECT,
        related_name="orders",
        help_text="Клиент, оформивший заказ",
    )

    # Статус заказа
    status = models.CharField(
        max_length=20,
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.NEW,
        help_text="Статус заказа: новый, в обработке, подтвержден, отменен, выполнен",
    )

    # Способ получения
    delivery_type = models.CharField(
        max_length=20,
        choices=DeliveryTypeChoices.choices,
        default=DeliveryTypeChoices.PICKUP,
        help_text="Способ получения заказа: самовывоз или доставка",
    )

    # Контактная информация
    contact_email = models.EmailField(
        help_text="Контактный email для этого заказа (может отличаться от email клиента)"
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Контактный телефон для этого заказа",
    )
    first_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Имя получателя",
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Фамилия получателя",
    )
    address = models.TextField(
        blank=True,
        help_text="Адрес доставки (обязателен при delivery_type=delivery)",
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Широта точки доставки (обязательна при delivery_type=delivery)",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Долгота точки доставки (обязательна при delivery_type=delivery)",
    )

    # Дополнительные примечания
    notes = models.TextField(
        blank=True,
        help_text="Примечания к заказу или особые инструкции",
    )

    class Meta:
        db_table = "orders"
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["status"]),
            models.Index(fields=["delivery_type"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["order_number"]),
        ]

    def __str__(self) -> str:
        return f"Order {self.order_number or self.pk} - {self.status}"

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

    # Снимок названия товара на момент заказа
    product_name = models.CharField(
        max_length=255,
        help_text="Название товара на момент заказа",
    )

    # Количество и цена
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Количество товара",
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Цена за единицу на момент заказа",
    )

    class Meta:
        db_table = "order_items"
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"
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
