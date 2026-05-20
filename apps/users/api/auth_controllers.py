"""Роутер /api/auth/ — реализация контрактов contracts/auth/*.json."""

from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from ninja import Router
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.shared.errors import (
    email_already_taken,
    invalid_credentials,
    invalid_token,
    validation_error,
)
from apps.users.api.auth_schemas import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserSchema,
)
from apps.users.api.ninja_auth import customer_auth
from apps.users.constants import RoleName
from apps.users.models import Customer
from apps.users.services.customer_service import CustomerService
from apps.users.services.password_reset_service import consume_reset, request_reset
from apps.users.services.role_service import RoleService

router = Router(tags=["Auth"])


# ============================================================================
# Helpers
# ============================================================================


def _user_payload(customer: Customer) -> dict:
    """Сериализовать customer в формат UserSchema (он же `user` в ответах)."""
    return {
        "id": str(customer.id),
        "username": customer.username,
        "email": customer.email,
        "created_at": customer.created_at,
    }


def _password_validation_errors(password: str, confirmation: str) -> dict:
    """Бизнес-валидация пароля поверх Pydantic-минимума (8 символов).

    Контракт требует "минимум 8 символов и хотя бы одну цифру",
    а также совпадение password_confirmation.
    """
    fields: dict[str, list[str]] = {}
    if not any(ch.isdigit() for ch in password):
        fields["password"] = [
            "Пароль должен содержать минимум 8 символов и хотя бы одну цифру"
        ]
    if password != confirmation:
        fields["password_confirmation"] = ["Пароли не совпадают"]
    return fields


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/register", response={201: AuthResponse}, summary="Регистрация")
@ratelimit(key="ip", rate="10/m", method="POST", block=True)
@transaction.atomic
def register(request: HttpRequest, data: RegisterRequest):
    errors = _password_validation_errors(data.password, data.password_confirmation)
    if errors:
        raise validation_error(errors)

    if CustomerService.email_exists(data.email):
        raise email_already_taken()

    customer = CustomerService.create_customer(
        email=data.email,
        password=data.password,
        username=data.username,
    )
    RoleService.assign_role(customer, RoleName.CUSTOMER)
    customer.update_last_login()

    tokens = CustomerService.generate_tokens(customer)
    return 201, {**tokens, "user": _user_payload(customer)}


@router.post("/login", response=AuthResponse, summary="Вход")
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def login(request: HttpRequest, data: LoginRequest):
    customer = CustomerService.authenticate(data.email, data.password)
    if customer is None:
        raise invalid_credentials()

    customer.update_last_login()
    tokens = CustomerService.generate_tokens(customer)
    return {**tokens, "user": _user_payload(customer)}


@router.post("/refresh", response=dict, summary="Обновление токенов")
@ratelimit(key="ip", rate="20/m", method="POST", block=True)
def refresh_tokens(request: HttpRequest, data: RefreshRequest):
    try:
        refresh = RefreshToken(data.refresh_token)
        # SimpleJWT с BLACKLIST_AFTER_ROTATION=True добавит старый токен
        # в blacklist при создании нового. Делаем явно через blacklist().
        refresh.blacklist()
    except (InvalidToken, TokenError):
        raise invalid_token("Refresh-токен недействителен или истёк")

    customer_id = refresh.get("customer_id")
    customer = CustomerService.get_customer_with_roles(customer_id)
    if customer is None:
        raise invalid_token("Refresh-токен недействителен или истёк")

    # Помечаем старую outstanding-запись как отозванную.
    from apps.users.models import CustomerOutstandingToken

    CustomerOutstandingToken.objects.filter(jti=refresh["jti"]).update(
        revoked_at=timezone.now()
    )

    tokens = CustomerService.generate_tokens(customer)
    # /refresh не возвращает user (см. contracts/auth/refresh.json)
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": tokens["token_type"],
        "expires_in": tokens["expires_in"],
    }


@router.post("/logout", auth=customer_auth, response={204: None}, summary="Выход")
def logout(request: HttpRequest, data: LogoutRequest = None):
    """Отзывает либо конкретный refresh (если передан), либо все активные.

    По контракту тело необязательное.
    """
    customer: Customer = request.auth

    if data and data.refresh_token:
        try:
            RefreshToken(data.refresh_token).blacklist()
        except (InvalidToken, TokenError):
            # Тихо игнорируем — клиент мог отправить уже невалидный токен.
            pass
    else:
        _revoke_all_customer_sessions(customer)

    return 204, None


@router.get("/me", auth=customer_auth, response=UserSchema, summary="Текущий пользователь")
def me(request: HttpRequest):
    return _user_payload(request.auth)


@router.post(
    "/forgot-password",
    response=MessageResponse,
    summary="Запрос восстановления пароля",
)
@ratelimit(key="ip", rate="3/m", method="POST", block=True)
def forgot_password(request: HttpRequest, data: ForgotPasswordRequest):
    """Всегда отвечаем 200 — защита от энумерации (см. контракт)."""
    request_reset(data.email)
    return {
        "message": (
            "Если email зарегистрирован, на него отправлено письмо "
            "со ссылкой для сброса пароля"
        )
    }


@router.post(
    "/reset-password",
    response=MessageResponse,
    summary="Сброс пароля по токену",
)
def reset_password(request: HttpRequest, data: ResetPasswordRequest):
    errors = _password_validation_errors(data.password, data.password_confirmation)
    if errors:
        raise validation_error(errors)

    customer = consume_reset(data.token, data.password)
    _revoke_all_customer_sessions(customer)
    return {"message": "Пароль изменён. Войдите с новым паролем"}


def _revoke_all_customer_sessions(customer: Customer) -> None:
    """Blacklist все непогашенные refresh-токены клиента.

    Используется при logout без body и при reset-password. Перебирает
    CustomerOutstandingToken (наш реестр) и создаёт BlacklistedToken
    через простую OutstandingToken-запись на каждый jti.
    """
    from django.utils import timezone
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    from apps.users.models import CustomerOutstandingToken

    now = timezone.now()
    active = CustomerOutstandingToken.objects.filter(
        customer=customer, revoked_at__isnull=True
    )
    for cot in active:
        ot, _ = OutstandingToken.objects.get_or_create(
            jti=cot.jti,
            defaults={
                "token": "",
                "expires_at": cot.expires_at,
            },
        )
        BlacklistedToken.objects.get_or_create(token=ot)
        cot.revoked_at = now
        cot.save(update_fields=["revoked_at"])
