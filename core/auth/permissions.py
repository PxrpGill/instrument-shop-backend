"""
Custom permission classes for Django Ninja RBAC system.
"""
from typing import TYPE_CHECKING
from apps.users.models import Customer
from core.auth.exceptions import PermissionDeniedError, InsufficientPrivilegesError

if TYPE_CHECKING:
    from ninja import Request


class RolePermission:
    """
    Permission class that requires user to have at least one of the specified roles.
    Usage: @api.get("/endpoint", permissions=[RolePermission('admin', 'manager')])
    """

    def __init__(self, *role_names: str):
        self.role_names = role_names

    def __call__(self, request: "Request", operation) -> bool:
        customer = getattr(request, 'customer', None)
        if not customer:
            return False

        for role_name in self.role_names:
            if customer.has_role(role_name):
                return True
        return False


class HasPermission:
    """
    Permission class that requires user to have specific permission(s).
    """

    def __init__(self, *permissions: str, require_all: bool = True):
        self.permissions = permissions
        self.require_all = require_all

    def __call__(self, request: "Request", operation) -> bool:
        customer = getattr(request, 'customer', None)
        if not customer:
            return False

        if self.require_all:
            for perm in self.permissions:
                if not customer.has_permission(perm):
                    return False
            return True
        else:
            for perm in self.permissions:
                if customer.has_permission(perm):
                    return True
            return False


class IsAdmin(RolePermission):
    """Shortcut for admin-only access."""

    def __init__(self):
        super().__init__('admin')


class IsAuthenticated:
    """Ensures the request is made by an authenticated user."""

    def __call__(self, request: "Request", operation) -> bool:
        return hasattr(request, 'customer') and request.customer is not None


class HasRoleMixin:
    """Mixin providing role checking utilities."""

    @staticmethod
    def get_customer_from_request(request: "Request") -> Customer:
        customer = getattr(request, 'customer', None)
        if not customer:
            raise ValueError("Authentication required")
        return customer

    @staticmethod
    def require_role(customer: Customer, *role_names: str) -> bool:
        for role_name in role_names:
            if customer.has_role(role_name):
                return True
        raise InsufficientPrivilegesError(
            f"Требуется одна из ролей: {', '.join(role_names)}"
        )

    @staticmethod
    def require_permission(customer: Customer, *permissions: str, require_all: bool = True) -> bool:
        if customer.has_role('admin'):
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
