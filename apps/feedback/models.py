"""Модель обращений с формы обратной связи.

Контракт: contracts/feedback/submit.json (POST /api/feedback, без auth).

`ip_address` хранится для антиспама и аналитики. `processed_at` — отметка
менеджера, что обращение обработано (заполняется в админке).
"""

from __future__ import annotations

from django.db import models


class FeedbackMessage(models.Model):
    """Одно обращение с публичной формы /feedback."""

    full_name = models.CharField(
        max_length=100,
        verbose_name="Имя",
    )
    email = models.EmailField(
        verbose_name="Email",
    )
    phone = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="Телефон",
        help_text="Российский формат, например +7 (999) 999-99-99.",
    )
    message = models.TextField(
        verbose_name="Сообщение",
        help_text="1..2000 символов.",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP-адрес",
        help_text="IP отправителя на момент создания обращения (для антиспама).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано",
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Обработано",
        help_text="Дата отметки об обработке менеджером.",
    )

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["processed_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email}) — {self.created_at:%Y-%m-%d}"

    @property
    def is_processed(self) -> bool:
        return self.processed_at is not None
