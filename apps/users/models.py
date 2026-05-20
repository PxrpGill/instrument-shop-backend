import secrets
import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone


class Role(models.Model):
    """
    Модель роли для системы RBAC.
    Определяет набор разрешений для определенной роли.
    """

    name = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(
        default=dict,
        help_text="JSON объект с разрешениями, например: {'create_product': true, 'edit_product': true}"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:
        return self.name

    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission."""
        if '*' in self.permissions:
            return True
        return self.permissions.get(permission, False)

    def get_all_permissions(self) -> dict:
        """Get all permissions for this role."""
        return self.permissions.copy()


class CustomerRole(models.Model):
    """
    Промежуточная модель для связи Customer и Role.
    Отслеживает кто и когда назначил роль.
    """

    customer = models.ForeignKey(
        'Customer',
        on_delete=models.CASCADE,
        related_name='customer_roles'
    )
    role = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE,
        related_name='role_customers'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        'Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_customer_roles'
    )

    class Meta:
        db_table = 'customer_roles'
        verbose_name = 'Роль клиента'
        verbose_name_plural = 'Роли клиентов'
        unique_together = ['customer', 'role']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['role']),
            models.Index(fields=['assigned_at']),
        ]

    def __str__(self) -> str:
        return f"{self.customer.email} -> {self.role.name}"


class Customer(models.Model):
    """
    Модель клиента магазина.
    Полностью отделена от системных пользователей (Django User).
    Используется для авторизации клиентов в API магазина.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Имя пользователя для отображения (2..64 символа). Заполняется при регистрации.",
    )
    phone = models.CharField(max_length=20, blank=True, db_index=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    # Пароль (хранится в хешированном виде)
    password_hash = models.CharField(max_length=255)

    # Ролевая система
    roles = models.ManyToManyField(
        'Role',
        through='CustomerRole',
        through_fields=('customer', 'role'),
        related_name='customers',
        blank=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'customers'
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
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
        return ""

    def update_last_login(self):
        """Обновляет время последнего входа."""
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])

    def has_role(self, role_name: str) -> bool:
        """Check if customer has specific role."""
        return self.roles.filter(name=role_name, is_active=True).exists()

    def has_permission(self, permission: str) -> bool:
        """Check if customer has specific permission through any of their roles."""
        for role in self.roles.filter(is_active=True).prefetch_related(None):
            if role.has_permission(permission):
                return True
        return False

    def get_roles(self):
        """Get all roles for this customer."""
        return self.roles.filter(is_active=True)

    def get_permissions(self) -> dict:
        """Get all permissions from all roles (combined)."""
        permissions = {}
        for role in self.roles.filter(is_active=True).prefetch_related(None):
            for permission_name, is_allowed in role.get_all_permissions().items():
                if permission_name == '*':
                    permissions['*'] = bool(is_allowed)
                    continue
                permissions[permission_name] = permissions.get(permission_name, False) or bool(is_allowed)
        return permissions


PASSWORD_RESET_TOKEN_TTL = timedelta(minutes=30)


def _generate_reset_token() -> str:
    """Криптостойкий URL-safe токен ~43 символа (32 байта энтропии)."""
    return secrets.token_urlsafe(32)


class PasswordResetToken(models.Model):
    """Одноразовый токен для сброса пароля.

    Жизненный цикл:
    - Создаётся в forgot-password сервисом, отправляется ссылкой на email.
    - Используется в reset-password: проверяется срок и used_at, проставляется used_at.
    - Повторное использование запрещено (used_at не пустой → INVALID_TOKEN).
    """

    token = models.CharField(
        max_length=64,
        unique=True,
        default=_generate_reset_token,
        verbose_name="Токен",
    )
    customer = models.ForeignKey(
        "Customer",
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
        verbose_name="Клиент",
    )
    expires_at = models.DateTimeField(verbose_name="Истекает")
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Использован",
        help_text="Если заполнен — токен уже был использован и больше не валиден.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")

    class Meta:
        db_table = "password_reset_tokens"
        verbose_name = "Токен сброса пароля"
        verbose_name_plural = "Токены сброса пароля"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["customer", "used_at"]),
        ]

    def __str__(self) -> str:
        state = "использован" if self.used_at else "активен"
        return f"reset для {self.customer.email} ({state})"

    @classmethod
    def issue_for(cls, customer: "Customer") -> "PasswordResetToken":
        """Создать новый токен и проставить срок жизни."""
        return cls.objects.create(
            customer=customer,
            expires_at=timezone.now() + PASSWORD_RESET_TOKEN_TTL,
        )

    @property
    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at > timezone.now()

    def mark_used(self) -> None:
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])


class CustomerOutstandingToken(models.Model):
    """Наш реестр активных refresh-токенов клиента.

    SimpleJWT.token_blacklist ведёт свой OutstandingToken с user FK на
    auth.User (int) — несовместимо с нашим Customer (UUID). Поэтому мы
    отдельно трекаем выпущенные refresh-токены, чтобы при logout без body
    или reset-password можно было отозвать все активные сессии.
    """

    customer = models.ForeignKey(
        "Customer",
        on_delete=models.CASCADE,
        related_name="outstanding_tokens",
        verbose_name="Клиент",
    )
    jti = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="JTI",
        help_text="JWT ID — уникальный идентификатор refresh-токена.",
    )
    expires_at = models.DateTimeField(verbose_name="Истекает")
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name="Выпущен")
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Отозван",
        help_text="Заполнен — токен помещён в blacklist.",
    )

    class Meta:
        db_table = "customer_outstanding_tokens"
        verbose_name = "Активный refresh-токен"
        verbose_name_plural = "Активные refresh-токены"
        ordering = ["-issued_at"]
        indexes = [
            models.Index(fields=["customer", "revoked_at"]),
            models.Index(fields=["jti"]),
        ]

    def __str__(self) -> str:
        state = "отозван" if self.revoked_at else "активен"
        return f"{self.customer.email} :: {self.jti[:8]}... ({state})"
