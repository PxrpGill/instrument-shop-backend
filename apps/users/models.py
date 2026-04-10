from django.db import models
from django.utils import timezone
import uuid


class Customer(models.Model):
    """
    Модель клиента магазина.
    Полностью отделена от системных пользователей (Django User).
    Используется для авторизации клиентов в API магазина.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, db_index=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    
    # Пароль (хранится в хешированном виде)
    password_hash = models.CharField(max_length=255)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'customers'
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        """Возвращает полное имя клиента."""
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.email

    def update_last_login(self):
        """Обновляет время последнего входа."""
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])