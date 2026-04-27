"""
Service layer for Role management.
"""

from typing import Optional, List, Dict, Any
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from apps.users.models import Customer, Role, CustomerRole
from apps.users.constants import Permission, RoleName
from core.auth.exceptions import (
    PermissionDeniedError,
    RoleNotFoundError,
    CustomerRoleAssignmentError,
    InsufficientPrivilegesError,
)


class RoleService:
    """Сервис для работы с ролями и permissions."""

    @staticmethod
    def get_role_by_name(role_name: str) -> Optional[Role]:
        """Получение роли по имени."""
        return Role.objects.filter(name=role_name, is_active=True).first()

    @staticmethod
    def get_role_by_id(role_id: int) -> Optional[Role]:
        """Получение роли по ID."""
        return Role.objects.filter(id=role_id, is_active=True).first()

    @staticmethod
    def get_all_roles() -> List[Role]:
        """Получение всех активных ролей."""
        return Role.objects.filter(is_active=True).order_by("name")

    @staticmethod
    def create_role(
        name: str,
        permissions: Dict[str, bool],
        description: str = "",
        created_by: Optional[Customer] = None,
    ) -> Role:
        """Создание новой роли."""
        if Role.objects.filter(name=name).exists():
            raise CustomerRoleAssignmentError(f"Роль с именем '{name}' уже существует")

        role = Role.objects.create(
            name=name, permissions=permissions, description=description
        )
        return role

    @staticmethod
    def update_role(
        role: Role, permissions: Dict[str, bool], description: str = None
    ) -> Role:
        """Обновление роли."""
        role.permissions = permissions
        if description is not None:
            role.description = description
        role.save()
        return role

    @staticmethod
    def delete_role(role: Role) -> bool:
        """Удаление роли (soft delete - деактивация)."""
        role.is_active = False
        role.save()
        return True

    @staticmethod
    def get_customer_roles(customer: Customer) -> List[Role]:
        """Получение всех ролей клиента."""
        return list(customer.roles.filter(is_active=True))

    @staticmethod
    def get_customer_permissions(customer: Customer) -> Dict[str, bool]:
        """Получение всех разрешений клиента из всех его ролей."""
        return customer.get_permissions()

    @staticmethod
    @transaction.atomic
    def assign_role(
        customer: Customer, role_name: str, assigned_by: Optional[Customer] = None
    ) -> CustomerRole:
        """
        Назначение роли клиенту.

        Args:
            customer: Клиент которому назначаем роль
            role_name: Имя роли
            assigned_by: Кто назначил (администратор)

        Returns:
            CustomerRole объект

        Raises:
            RoleNotFoundError: если роль не найдена
            CustomerRoleAssignmentError: если роль уже назначена
        """
        role = RoleService.get_role_by_name(role_name)
        if not role:
            raise RoleNotFoundError(role_name)

        # Проверяем, не назначена ли уже эта роль
        if CustomerRole.objects.filter(customer=customer, role=role).exists():
            raise CustomerRoleAssignmentError(
                f"Роль '{role_name}' уже назначена клиенту {customer.email}"
            )

        customer_role = CustomerRole.objects.create(
            customer=customer, role=role, assigned_by=assigned_by
        )
        return customer_role

    @staticmethod
    @transaction.atomic
    def remove_role(
        customer: Customer, role_name: str, removed_by: Optional[Customer] = None
    ) -> bool:
        """
        Удаление роли у клиента.

        Args:
            customer: Клиент у которого удаляем роль
            role_name: Имя роли
            removed_by: Кто удалил (администратор)

        Returns:
            True если роль была удалена, False если не было

        Raises:
            RoleNotFoundError: если роль не найдена
        """
        role = RoleService.get_role_by_name(role_name)
        if not role:
            raise RoleNotFoundError(role_name)

        deleted, _ = CustomerRole.objects.filter(customer=customer, role=role).delete()

        return deleted > 0

    @staticmethod
    def has_role(customer: Customer, role_name: str) -> bool:
        """Проверка наличия роли у клиента."""
        return customer.roles.filter(name=role_name, is_active=True).exists()

    @staticmethod
    def has_permission(customer: Customer, permission: str) -> bool:
        """
        Проверка наличия разрешения у клиента.

        Args:
            customer: Клиент
            permission: Название разрешения

        Returns:
            True если клиент имеет разрешение
        """
        # Админы имеют все разрешения
        if customer.has_role(RoleName.ADMIN):
            return True

        # Проверяем через роли
        return customer.has_permission(permission)

    @staticmethod
    def require_role(customer: Customer, *role_names: str) -> bool:
        """
        Проверка наличия хотя бы одной из ролей.
        Выбрасывает InsufficientPrivilegesError если нет ни одной.
        """
        for role_name in role_names:
            if customer.has_role(role_name):
                return True
        raise InsufficientPrivilegesError(
            f"Требуется одна из ролей: {', '.join(role_names)}"
        )

    @staticmethod
    def require_permission(
        customer: Customer, *permissions: str, require_all: bool = True
    ) -> bool:
        """
        Проверка наличия разрешений.
        Выбрасывает PermissionDeniedError если недостаточно прав.

        Args:
            customer: Клиент
            permissions: Список требуемых разрешений
            require_all: True если нужны все разрешения, False если хотя бы одно
        """
        if customer.has_role(RoleName.ADMIN):
            return True

        if require_all:
            for perm in permissions:
                if not customer.has_permission(perm):
                    raise PermissionDeniedError(f"Требуется разрешение: {perm}")
            return True
        else:
            for perm in permissions:
                if customer.has_permission(perm):
                    return True
            raise PermissionDeniedError(
                f"Требуется хотя бы одно из разрешений: {', '.join(permissions)}"
            )

    @staticmethod
    def get_customers_with_role(role_name: str) -> List[Customer]:
        """Получение всех клиентов с указанной ролью."""
        role = RoleService.get_role_by_name(role_name)
        if not role:
            return []
        return list(role.customers.filter(is_active=True))

    @staticmethod
    def get_customers_with_permission(permission: str) -> List[Customer]:
        """Получение всех клиентов имеющих указанное разрешение."""
        customers = []
        for role in Role.objects.filter(is_active=True):
            if role.has_permission(permission):
                customers.extend(role.customers.filter(is_active=True))
        return list(set(customers))

    @staticmethod
    def initialize_default_roles() -> Dict[str, Role]:
        """
        Создание стандартных ролей системы.

        Returns:
            Словарь созданных ролей
        """
        default_roles = {
            RoleName.CUSTOMER: {
                "description": "Обычный клиент - может только просматривать товары и управлять профилем",
                "permissions": {
                    Permission.VIEW_PRODUCT: True,
                    Permission.VIEW_CATEGORY: True,
                    Permission.VIEW_OWN_PROFILE: True,
                    Permission.EDIT_OWN_PROFILE: True,
                    Permission.CREATE_ORDER: True,
                },
            },
            RoleName.CATALOG_MANAGER: {
                "description": "Менеджер каталога - управление товарами, категориями и публикациями",
                "permissions": {
                    Permission.VIEW_PRODUCT: True,
                    Permission.CREATE_PRODUCT: True,
                    Permission.EDIT_PRODUCT: True,
                    Permission.DELETE_PRODUCT: True,
                    Permission.PUBLISH_PRODUCT: True,
                    Permission.MANAGE_AVAILABILITY: True,
                    Permission.VIEW_CATEGORY: True,
                    Permission.CREATE_CATEGORY: True,
                    Permission.EDIT_CATEGORY: True,
                    Permission.DELETE_CATEGORY: True,
                    Permission.VIEW_CUSTOMER: True,
                },
            },
            RoleName.ADMIN: {
                "description": "Администратор - полный доступ ко всем функциям системы",
                "permissions": {Permission.WILDCARD: True},  # Wildcard - все разрешения
            },
        }

        created_roles = {}
        for role_name, role_data in default_roles.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={
                    "description": role_data["description"],
                    "permissions": role_data["permissions"],
                    "is_active": True,
                },
            )
            created_roles[role_name] = role

        return created_roles
