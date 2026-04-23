"""
API controllers for role management.
Admin-only endpoints for managing roles and user assignments.
"""
from typing import List
from django.http import HttpRequest
from ninja import Router
from django.db import transaction

from apps.users.models import Customer, Role, CustomerRole
from apps.users.services.role_service import RoleService
from apps.users.api.schemas import (
    RoleSchema,
    RoleCreateSchema,
    RoleUpdateSchema,
    RoleAssignmentSchema,
    CustomerRoleListSchema,
    MessageResponse,
)
from apps.users.api.controllers import get_customer_from_request
from core.auth.exceptions import PermissionDeniedError, RoleNotFoundError

router = Router(tags=["Admin - Roles"])


def require_admin(request: HttpRequest) -> Customer:
    """Authenticate and ensure the user is an admin."""
    customer = get_customer_from_request(request)
    if not customer.has_role('admin'):
        raise PermissionDeniedError("Требуется роль администратора")
    return customer


@router.get("/roles/", response=List[RoleSchema], summary="Список всех ролей (Admin only)")
def list_roles(request: HttpRequest) -> List[Role]:
    """
    Получение списка всех ролей.
    Доступно только администраторам.
    """
    require_admin(request)
    return RoleService.get_all_roles()


@router.get("/roles/{int:role_id}", response=RoleSchema, summary="Получение роли (Admin only)")
def get_role(request: HttpRequest, role_id: int) -> Role:
    """
    Получение информации о конкретной роли.
    Доступно только администраторам.
    """
    require_admin(request)
    role = RoleService.get_role_by_id(role_id)
    if not role:
        raise RoleNotFoundError(str(role_id))
    return role


@router.post("/roles/", response=RoleSchema, summary="Создание новой роли (Admin only)")
def create_role(request: HttpRequest, payload: RoleCreateSchema) -> Role:
    """
    Создание новой роли.
    Доступно только администраторам.

    Пример permissions:
    {
        "create_product": true,
        "edit_product": false,
        "*": false  // Wildcard - все разрешения
    }
    """
    require_admin(request)
    role = RoleService.create_role(
        name=payload.name,
        description=payload.description or "",
        permissions=payload.permissions,
        created_by=get_customer_from_request(request)
    )
    return role


@router.put("/roles/{int:role_id}", response=RoleSchema, summary="Обновление роли (Admin only)")
def update_role(request: HttpRequest, role_id: int, payload: RoleUpdateSchema) -> Role:
    """
    Обновление существующей роли.
    Доступно только администраторам.
    """
    require_admin(request)
    role = RoleService.get_role_by_id(role_id)
    if not role:
        raise RoleNotFoundError(str(role_id))

    role = RoleService.update_role(
        role=role,
        permissions=payload.permissions,
        description=payload.description
    )
    return role


@router.delete("/roles/{int:role_id}", response=MessageResponse, summary="Удаление роли (Admin only)")
def delete_role(request: HttpRequest, role_id: int) -> dict:
    """
    Деактивация роли (soft delete).
    Роль не удаляется из БД, но становится неактивной.
    Доступно только администраторам.
    """
    require_admin(request)
    role = RoleService.get_role_by_id(role_id)
    if not role:
        raise RoleNotFoundError(str(role_id))

    # Нельзя удалить системные роли
    system_roles = ['admin', 'customer']
    if role.name in system_roles:
        raise PermissionDeniedError(f"Нельзя удалить системную роль '{role.name}'")

    RoleService.delete_role(role)
    return {"message": f"Роль '{role.name}' успешно деактивирована"}


# ============================================================================
# Customer Role Assignments
# ============================================================================

@router.get("/customers/{customer_id}/roles/", response=List[CustomerRoleListSchema], summary="Роли клиента (Admin only)")
def get_customer_roles(request: HttpRequest, customer_id: str) -> List[CustomerRoleListSchema]:
    """
    Получение списка ролей назначенных клиенту.
    Доступно только администраторам.
    """
    require_admin(request)
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        raise RoleNotFoundError(f"Клиент с ID {customer_id} не найден")

    customer_roles = customer.customer_roles.select_related('role', 'assigned_by').all()
    return [CustomerRoleListSchema.from_model(cr) for cr in customer_roles]


@router.post("/customers/{customer_id}/roles/", response=CustomerRoleListSchema, summary="Назначение роли клиенту (Admin only)")
def assign_role_to_customer(
    request: HttpRequest,
    customer_id: str,
    payload: RoleAssignmentSchema
) -> CustomerRoleListSchema:
    """
    Назначение роли клиенту.
    Доступно только администраторам.
    """
    require_admin(request)
    try:
        customer = Customer.objects.get(id=customer_id, is_active=True)
    except Customer.DoesNotExist:
        raise RoleNotFoundError(f"Клиент с ID {customer_id} не найден")

    customer_role = RoleService.assign_role(
        customer=customer,
        role_name=payload.role_name,
        assigned_by=get_customer_from_request(request)
    )

    # Reload with related fields for response
    customer_role = CustomerRole.objects.select_related('role', 'assigned_by').get(id=customer_role.id)
    return CustomerRoleListSchema.from_model(customer_role)


@router.delete(
    "/customers/{customer_id}/roles/{role_name}/",
    response=MessageResponse,
    summary="Удаление роли у клиента (Admin only)"
)
def remove_role_from_customer(
    request: HttpRequest,
    customer_id: str,
    role_name: str
) -> dict:
    """
    Удаление роли у клиента.
    Доступно только администраторам.
    """
    require_admin(request)
    try:
        customer = Customer.objects.get(id=customer_id, is_active=True)
    except Customer.DoesNotExist:
        raise RoleNotFoundError(f"Клиент с ID {customer_id} не найден")

    # Проверяем, не пытается ли админ удалить себе роль admin
    if customer == get_customer_from_request(request) and role_name == 'admin':
        raise PermissionDeniedError("Нельзя удалить у себя роль администратора")

    removed = RoleService.remove_role(
        customer=customer,
        role_name=role_name,
        removed_by=get_customer_from_request(request)
    )

    if not removed:
        raise RoleNotFoundError(f"Роль '{role_name}' не была назначена клиенту")

    return {"message": f"Роль '{role_name}' успешно удалена у клиента {customer.email}"}


@router.get("/customers/{customer_id}/permissions/", response=dict, summary="Разрешения клиента (Admin only)")
def get_customer_permissions(request: HttpRequest, customer_id: str) -> dict:
    """
    Получение всех разрешений клиента.
    Доступно только администраторам.
    """
    require_admin(request)
    try:
        customer = Customer.objects.get(id=customer_id, is_active=True)
    except Customer.DoesNotExist:
        raise RoleNotFoundError(f"Клиент с ID {customer_id} не найден")

    permissions = RoleService.get_customer_permissions(customer)
    roles = list(customer.roles.filter(is_active=True).values_list('name', flat=True))

    return {
        "customer_id": str(customer.id),
        "email": customer.email,
        "roles": roles,
        "permissions": permissions
    }
