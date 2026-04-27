from ninja import Router
from ninja.errors import HttpError
from django.http import HttpRequest
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .schemas import (
    CustomerRegisterRequest,
    CustomerLoginRequest,
    CustomerProfileResponse,
    CustomerUpdateRequest,
    TokenResponse,
    TokenRefreshRequest,
    ChangePasswordRequest,
)
from apps.users.constants import RoleName
from apps.users.services.customer_service import CustomerService
from apps.users.models import Customer

router = Router(tags=["Customers"])


def get_customer_from_request(request: HttpRequest) -> Customer:
    """Получение текущего клиента из запроса."""
    # Find Authorization header (case-insensitive search)
    auth_header = ""
    for key in request.META:
        if key.upper() == "HTTP_AUTHORIZATION":
            auth_header = request.META[key]
            break

    if not auth_header:
        raise HttpError(status_code=401, message="Требуется авторизация")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HttpError(status_code=401, message="Неверный формат токена")

    token_str = parts[1]

    try:
        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken(token_str)
        user_id = token.get("user_id")

        if not user_id:
            raise HttpError(status_code=401, message="Невалидный токен")

        customer = Customer.objects.prefetch_related("roles").get(
            id=user_id, is_active=True
        )
        return customer

    except (InvalidToken, TokenError, Customer.DoesNotExist) as e:
        raise HttpError(status_code=401, message="Невалидный токен")


@router.post("/register", response=TokenResponse, summary="Регистрация нового клиента")
@transaction.atomic
def register(request: HttpRequest, data: CustomerRegisterRequest) -> TokenResponse:
    """
    Регистрация нового клиента.
    Возвращает JWT токены для доступа к API.
    """
    if CustomerService.email_exists(data.email):
        raise HttpError(status_code=400, message="Email уже зарегистрирован")

    customer = CustomerService.create_customer(
        email=data.email,
        password=data.password,
        phone=data.phone,
        first_name=data.first_name,
        last_name=data.last_name,
    )

    from apps.users.services.role_service import RoleService

    RoleService.assign_role(customer, RoleName.CUSTOMER)

    tokens = CustomerService.generate_tokens(customer)
    customer.update_last_login()

    return TokenResponse(
        access=tokens["access"],
        refresh=tokens["refresh"],
    )


@router.post("/login", response=TokenResponse, summary="Вход клиента")
def login(request: HttpRequest, data: CustomerLoginRequest) -> TokenResponse:
    """
    Вход клиента по email и паролю.
    Возвращает JWT токены для доступа к API.
    """
    customer = CustomerService.authenticate(data.email, data.password)

    if not customer:
        raise HttpError(status_code=401, message="Неверный email или пароль")

    tokens = CustomerService.generate_tokens(customer)
    customer.update_last_login()

    return TokenResponse(
        access=tokens["access"],
        refresh=tokens["refresh"],
    )


@router.post("/refresh", response=TokenResponse, summary="Обновление токена")
def refresh_token(request: TokenRefreshRequest) -> TokenResponse:
    """
    Обновление access токена с помощью refresh токена.
    """
    try:
        refresh = RefreshToken(request.refresh)
        customer_id = refresh.get("user_id")

        if not customer_id:
            raise HttpError(status_code=401, message="Невалидный токен")

        customer = CustomerService.get_customer_with_roles(customer_id)
        if not customer or not customer.is_active:
            raise HttpError(
                status_code=401, message="Пользователь не найден или неактивен"
            )

        tokens = CustomerService.generate_tokens(customer)

        return TokenResponse(
            access=tokens["access"],
            refresh=tokens["refresh"],
        )
    except (InvalidToken, TokenError) as e:
        raise HttpError(status_code=401, message="Невалидный или истекший токен")


@router.get("/me", response=CustomerProfileResponse, summary="Профиль текущего клиента")
def get_profile(request: HttpRequest) -> CustomerProfileResponse:
    """
    Получение профиля текущего авторизованного клиента.
    Требуется JWT токен в заголовке Authorization.
    """
    customer = get_customer_from_request(request)

    # Загружаем роли для возврата в ответе
    roles = list(customer.roles.filter(is_active=True).values_list("name", flat=True))
    permissions = customer.get_permissions()

    # Создаем response с дополнительными полями
    response = CustomerProfileResponse(
        id=str(customer.id),
        email=customer.email,
        phone=customer.phone,
        first_name=customer.first_name,
        last_name=customer.last_name,
        address=customer.address,
        is_active=customer.is_active,
        created_at=customer.created_at,
        last_login=customer.last_login,
        roles=roles,
        permissions=permissions,
    )
    return response


@router.patch("/me", response=CustomerProfileResponse, summary="Обновление профиля")
def update_profile(
    request: HttpRequest, data: CustomerUpdateRequest
) -> CustomerProfileResponse:
    """
    Обновление профиля текущего авторизованного клиента.
    """
    customer = get_customer_from_request(request)

    updated = CustomerService.update_customer(
        customer=customer,
        phone=data.phone,
        first_name=data.first_name,
        last_name=data.last_name,
        address=data.address,
    )

    # Возвращаем обновленный профиль
    roles = list(updated.roles.filter(is_active=True).values_list("name", flat=True))
    permissions = updated.get_permissions()

    return CustomerProfileResponse(
        id=str(updated.id),
        email=updated.email,
        phone=updated.phone,
        first_name=updated.first_name,
        last_name=updated.last_name,
        address=updated.address,
        is_active=updated.is_active,
        created_at=updated.created_at,
        last_login=updated.last_login,
        roles=roles,
        permissions=permissions,
    )


@router.post("/change-password", summary="Смена пароля")
def change_password(request: HttpRequest, data: ChangePasswordRequest) -> dict:
    """
    Смена пароля текущего авторизованного клиента.
    """
    customer = get_customer_from_request(request)

    success = CustomerService.change_password(
        customer,
        data.old_password,
        data.new_password,
    )

    if not success:
        raise HttpError(status_code=400, message="Неверный текущий пароль")

    return {"message": "Пароль успешно изменен"}
