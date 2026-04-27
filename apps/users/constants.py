"""
Centralized permission constants for RBAC system.

This module defines all permission strings used across the application.
Import these constants instead of using string literals in controllers and services.

Usage:
    from apps.users.constants import Permission
    # or
    from apps.users.constants import VIEW_PRODUCT, EDIT_PRODUCT
"""

from typing import Final


class Permission:
    """
    Permission constants for the RBAC system.

    Naming convention:
    - Use snake_case
    - Format: <action>_<resource>
    - Examples: view_product, edit_category
    """

    # Product permissions
    VIEW_PRODUCT: Final[str] = "view_product"
    CREATE_PRODUCT: Final[str] = "create_product"
    EDIT_PRODUCT: Final[str] = "edit_product"
    DELETE_PRODUCT: Final[str] = "delete_product"
    PUBLISH_PRODUCT: Final[str] = "publish_product"
    MANAGE_AVAILABILITY: Final[str] = "manage_availability"

    # Category permissions
    VIEW_CATEGORY: Final[str] = "view_category"
    CREATE_CATEGORY: Final[str] = "create_category"
    EDIT_CATEGORY: Final[str] = "edit_category"
    DELETE_CATEGORY: Final[str] = "delete_category"

    # Customer/User permissions
    VIEW_CUSTOMER: Final[str] = "view_customer"
    VIEW_OWN_PROFILE: Final[str] = "view_own_profile"
    EDIT_OWN_PROFILE: Final[str] = "edit_own_profile"

    # Order permissions
    VIEW_ORDER: Final[str] = "view_order"
    CREATE_ORDER: Final[str] = "create_order"
    EDIT_ORDER: Final[str] = "edit_order"
    CANCEL_ORDER: Final[str] = "cancel_order"
    MANAGE_ORDER_STATUS: Final[str] = "manage_order_status"

    # Wildcard - grants all permissions
    WILDCARD: Final[str] = "*"


# Convenience: export all permission strings as a list
ALL_PERMISSIONS: Final[list[str]] = [
    Permission.VIEW_PRODUCT,
    Permission.CREATE_PRODUCT,
    Permission.EDIT_PRODUCT,
    Permission.DELETE_PRODUCT,
    Permission.PUBLISH_PRODUCT,
    Permission.MANAGE_AVAILABILITY,
    Permission.VIEW_CATEGORY,
    Permission.CREATE_CATEGORY,
    Permission.EDIT_CATEGORY,
    Permission.DELETE_CATEGORY,
    Permission.VIEW_CUSTOMER,
    Permission.VIEW_OWN_PROFILE,
    Permission.EDIT_OWN_PROFILE,
    Permission.VIEW_ORDER,
    Permission.CREATE_ORDER,
    Permission.EDIT_ORDER,
    Permission.CANCEL_ORDER,
    Permission.MANAGE_ORDER_STATUS,
]


# Role name constants
class RoleName:
    """Role name constants."""

    CUSTOMER: Final[str] = "customer"
    CATALOG_MANAGER: Final[str] = "catalog_manager"
    ADMIN: Final[str] = "admin"


# For backward compatibility (manager -> catalog_manager migration)
LEGACY_MANAGER_ROLE: Final[str] = "manager"
