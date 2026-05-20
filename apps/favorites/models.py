"""Модель «Избранное».

Контракты:
- contracts/favorites/list.json — GET /api/favorites
- contracts/favorites/toggle.json — POST/DELETE /api/favorites/{product_id}

Запись принадлежит конкретному Customer; уникальность по паре (customer, product)
обеспечивает идемпотентность toggle (повторный POST не создаёт дубль).
"""

from __future__ import annotations

from django.db import models

from apps.products.models import Product
from apps.users.models import Customer


class Favorite(models.Model):
    """Товар в избранном у пользователя."""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Клиент",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Товар",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Добавлено")

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        unique_together = ("customer", "product")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.customer_id} → {self.product_id}"
