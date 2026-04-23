"""
Custom exceptions for RBAC system.
"""
from rest_framework import status
from ninja.errors import HttpError


class PermissionDeniedError(HttpError):
    """Raised when user doesn't have required permission."""

    def __init__(self, message: str = "У вас недостаточно прав для выполнения этого действия"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, message=message)


class RoleNotFoundError(HttpError):
    """Raised when role is not found."""

    def __init__(self, role_name: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"Роль '{role_name}' не найдена"
        )


class CustomerRoleAssignmentError(HttpError):
    """Raised when role assignment fails."""

    def __init__(self, message: str = "Не удалось назначить роль"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message
        )


class InsufficientPrivilegesError(HttpError):
    """Raised when user tries to perform privileged action without rights."""

    def __init__(self, message: str = "Недостаточно прав для выполнения этого действия"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message
        )
