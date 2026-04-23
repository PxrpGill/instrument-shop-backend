from ninja import Router
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
from .jwt_auth import CustomerJWTAuthentication
from apps.users.services.customer_service import CustomerService
from apps.users.models import Customer

router = Router(tags=["Customers"])

# JWT аутентификация для Ninja
jwt_auth = CustomerJWTAuthentication()


def get_customer_from_request(request: HttpRequest) -> Customer:
    """Получение текущего клиента из запроса."""
    auth_result = jwt_auth.authenticate(request)
    if not auth_result:
        raise ValueError("Требуется авторизация")
    customer, token = auth_result
    return customer


@router.post("/register", response=TokenResponse, summary="Регистрация нового клиента")
@transaction.atomic
def register(request: CustomerRegisterRequest) -> TokenResponse:
    """
    Регистрация нового клиента.
    Возвращает JWT токены для доступа к API.
    """
    if CustomerService.email_exists(request.email):
        raise ValueError("Email уже зарегистрирован")

    customer = CustomerService.create_customer(
        email=request.email,
        password=request.password,
        phone=request.phone,
        first_name=request.first_name,
        last_name=request.last_name,
    )

    from apps.users.services.role_service import RoleService
    RoleService.assign_role(customer, 'customer')

    tokens = CustomerService.generate_tokens(customer)
    customer.update_last_login()

    return TokenResponse(
        access=tokens['access'],
        refresh=tokens['refresh'],
    )


@router.post("/login", response=TokenResponse, summary="Вход клиента")
def login(request: CustomerLoginRequest) -> TokenResponse:
    """
    Вход клиента по email и паролю.
    Возвращает JWT токены для доступа к API.
    """
    customer = CustomerService.authenticate(request.email, request.password)

    if not customer:
        raise ValueError("Неверный email или пароль")

    tokens = CustomerService.generate_tokens(customer)
    customer.update_last_login()

    return TokenResponse(
        access=tokens['access'],
        refresh=tokens['refresh'],
    )


@router.post("/refresh", response=TokenResponse, summary="Обновление токена")
def refresh_token(request: TokenRefreshRequest) -> TokenResponse:
    """
    Обновление access токена с помощью refresh токена.
    """
    try:
        refresh = RefreshToken(request.refresh)
        customer_id = refresh.get('user_id')

        if not customer_id:
            raise ValueError("Невалидный токен")

        customer = CustomerService.get_customer_with_roles(customer_id)
        if not customer or not customer.is_active:
            raise ValueError("Пользователь не найден или неактивен")

        tokens = CustomerService.generate_tokens(customer)

        return TokenResponse(
            access=tokens['access'],
            refresh=tokens['refresh'],
        )
    except (InvalidToken, TokenError) as e:
        raise ValueError("Невалидный или истекший токен")


@router.get("/me", response=CustomerProfileResponse, summary="Профиль текущего клиента")
def get_profile(request: HttpRequest) -> CustomerProfileResponse:
    """
    Получение профиля текущего авторизованного клиента.
    Требуется JWT токен в заголовке Authorization.
    """
    customer = get_customer_from_request(request)

    # Загружаем роли для возврата в ответе
    roles = list(customer.roles.filter(is_active=True).values_list('name', flat=True))
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
def update_profile(request: HttpRequest, data: CustomerUpdateRequest) -> CustomerProfileResponse:
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
    roles = list(updated.roles.filter(is_active=True).values_list('name', flat=True))
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
        raise ValueError("Неверный текущий пароль")

    return {"message": "Пароль успешно изменен"}
