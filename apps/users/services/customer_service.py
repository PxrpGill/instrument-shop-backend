from typing import Optional

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password

from apps.users.models import Customer


class CustomerService:
    """Сервис для работы с клиентами."""

    @staticmethod
    def create_customer(
        email: str,
        password: str,
        username: str = "",
        phone: str = None,
        first_name: str = None,
        last_name: str = None,
    ) -> Customer:
        """Создание нового клиента."""
        password_hash = make_password(password)
        return Customer.objects.create(
            email=email,
            password_hash=password_hash,
            username=username,
            phone=phone or "",
            first_name=first_name or "",
            last_name=last_name or "",
        )

    @staticmethod
    def get_customer_by_email(email: str) -> Optional[Customer]:
        """Получение клиента по email."""
        return Customer.objects.filter(email__iexact=email).first()

    @staticmethod
    def get_customer_by_id(customer_id: str) -> Optional[Customer]:
        """Получение клиента по ID."""
        return Customer.objects.filter(id=customer_id).first()

    @staticmethod
    def get_customer_with_roles(customer_id: str) -> Optional[Customer]:
        """Получение клиента с предзагрузкой ролей."""
        return (
            Customer.objects.prefetch_related("roles")
            .filter(id=customer_id, is_active=True)
            .first()
        )

    @staticmethod
    def authenticate(email: str, password: str) -> Optional[Customer]:
        """Аутентификация клиента по email и паролю."""
        customer = CustomerService.get_customer_by_email(email)
        if not customer:
            return None
        if not customer.is_active:
            return None
        if not check_password(password, customer.password_hash):
            return None
        return customer

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля."""
        return check_password(plain_password, hashed_password)

    @staticmethod
    def generate_tokens(customer: Customer) -> dict:
        """Сгенерировать пару JWT по контракту /api/auth/login.

        Контракт: {access_token, refresh_token, token_type, expires_in}.
        expires_in — TTL access-токена в секундах из SIMPLE_JWT settings.
        """
        from rest_framework_simplejwt.tokens import RefreshToken

        from django.utils import timezone
        from rest_framework_simplejwt.utils import datetime_from_epoch

        refresh = RefreshToken()
        refresh["customer_id"] = str(customer.id)
        refresh["email"] = customer.email

        # Также прокидываем customer_id в access-токен, чтобы CustomerBearer
        # мог резолвить клиента без обращения к refresh.
        access = refresh.access_token
        access["customer_id"] = str(customer.id)
        access["email"] = customer.email

        # Регистрируем outstanding-запись для возможности отозвать все
        # активные сессии (logout без body / reset-password).
        from apps.users.models import CustomerOutstandingToken

        CustomerOutstandingToken.objects.create(
            customer=customer,
            jti=refresh["jti"],
            expires_at=datetime_from_epoch(refresh["exp"]),
        )

        return {
            "access_token": str(access),
            "refresh_token": str(refresh),
            "token_type": "Bearer",
            "expires_in": CustomerService.get_access_token_lifetime_seconds(),
        }

    @staticmethod
    def get_access_token_lifetime_seconds() -> int:
        return int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())

    @staticmethod
    def update_customer(
        customer: Customer,
        phone: str = None,
        first_name: str = None,
        last_name: str = None,
        address: str = None,
    ) -> Customer:
        """Обновление данных клиента."""
        if phone is not None:
            customer.phone = phone
        if first_name is not None:
            customer.first_name = first_name
        if last_name is not None:
            customer.last_name = last_name
        if address is not None:
            customer.address = address
        customer.save()
        return customer

    @staticmethod
    def change_password(
        customer: Customer, old_password: str, new_password: str
    ) -> bool:
        """Смена пароля клиента. Возвращает True при успехе."""
        if not CustomerService.verify_password(old_password, customer.password_hash):
            return False
        customer.password_hash = make_password(new_password)
        customer.save()
        return True

    @staticmethod
    def email_exists(email: str) -> bool:
        """Проверка существования email."""
        return Customer.objects.filter(email__iexact=email).exists()
