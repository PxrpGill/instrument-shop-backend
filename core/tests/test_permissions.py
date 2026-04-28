"""
Tests for core permission classes.
"""
import pytest
from ninja.testing import TestClient

from core.auth.permissions import (
    RolePermission,
    HasPermission,
    IsAdmin,
    IsAuthenticated,
    HasRoleMixin
)
from core.auth.exceptions import PermissionDeniedError, InsufficientPrivilegesError
from apps.users.models import Customer, Role
from apps.users.constants import RoleName
from apps.users.services.role_service import RoleService


class MockRequest:
    """Simple mock for Django Ninja request with customer attribute."""
    def __init__(self, customer=None):
        self.customer = customer


@pytest.mark.django_db
class TestRolePermission:
    """Tests for RolePermission class."""

    def test_permission_grants_if_customer_has_role(self, customer_factory):
        """Test permission passes when customer has required role."""
        customer = customer_factory()
        RoleService.assign_role(customer, RoleName.CATALOG_MANAGER)

        perm = RolePermission(RoleName.CATALOG_MANAGER)
        request = MockRequest(customer=customer)

        # Dummy operation (we just need permission check)
        operation = None
        assert perm(request, operation) is True

    def test_permission_denies_if_no_role(self, customer_factory):
        """Test permission fails when customer lacks required role."""
        customer = customer_factory()
        RoleService.assign_role(customer, "customer")

        perm = RolePermission("manager")
        request = MockRequest(customer=customer)

        assert perm(request, None) is False

    def test_permission_grants_if_multiple_roles_one_matches(self, customer_factory):
        """Test permission passes if customer has any of multiple roles."""
        customer = customer_factory()
        RoleService.assign_role(customer, RoleName.CATALOG_MANAGER)  # Has catalog_manager, needs admin or catalog_manager

        perm = RolePermission(RoleName.ADMIN, RoleName.CATALOG_MANAGER)
        request = MockRequest(customer=customer)

        assert perm(request, None) is True

    def test_permission_denies_if_unauthenticated(self):
        """Test permission fails when no customer attached."""
        perm = RolePermission("admin")
        request = MockRequest(customer=None)

        assert perm(request, None) is False


@pytest.mark.django_db
class TestHasPermission:
    """Tests for HasPermission class."""

    def test_permission_grants_when_customer_has_single_permission(self, customer_factory):
        """Test permission passes when customer has required permission."""
        customer = customer_factory()
        RoleService.create_role("editor", permissions={"edit_post": True})
        RoleService.assign_role(customer, "editor")

        perm = HasPermission("edit_post")
        request = MockRequest(customer=customer)

        assert perm(request, None) is True

    def test_permission_denies_when_customer_lacks_permission(self, customer_factory):
        """Test permission fails when customer lacks permission."""
        customer = customer_factory()
        RoleService.create_role("viewer", permissions={"view_post": True})
        RoleService.assign_role(customer, "viewer")

        perm = HasPermission("edit_post")
        request = MockRequest(customer=customer)

        assert perm(request, None) is False

    def test_permission_multiple_require_all(self, customer_factory):
        """Test require_all=True requires all permissions."""
        customer = customer_factory()
        RoleService.create_role("partial", permissions={"p1": True, "p2": False})
        RoleService.assign_role(customer, "partial")

        perm = HasPermission("p1", "p2", require_all=True)
        request = MockRequest(customer=customer)
        assert perm(request, None) is False  # Missing p2

        perm2 = HasPermission("p1", require_all=True)
        assert perm2(request, None) is True

    def test_permission_multiple_require_any(self, customer_factory):
        """Test require_all=False passes if any permission matches."""
        customer = customer_factory()
        RoleService.create_role("multi", permissions={"p1": True, "p2": True, "p3": False})
        RoleService.assign_role(customer, "multi")

        perm = HasPermission("p1", "p3", require_all=False)
        request = MockRequest(customer=customer)
        assert perm(request, None) is True  # p1 matches

        perm2 = HasPermission("p3", "p4", require_all=False)
        assert perm2(request, None) is False  # Neither matches

    def test_admin_bypasses_permission_check(self, customer_factory):
        """Test admin bypasses all permission checks."""
        customer = customer_factory()
        RoleService.assign_role(customer, "admin")

        perm = HasPermission("impossible_permission")
        request = MockRequest(customer=customer)
        assert perm(request, None) is True


@pytest.mark.django_db
class TestIsAdmin:
    """Tests for IsAdmin shortcut."""

    def test_admin_passes(self, customer_factory):
        customer = customer_factory()
        RoleService.assign_role(customer, "admin")
        perm = IsAdmin()
        request = MockRequest(customer=customer)
        assert perm(request, None) is True

    def test_non_admin_fails(self, customer_factory):
        customer = customer_factory()
        RoleService.assign_role(customer, "customer")
        perm = IsAdmin()
        request = MockRequest(customer=customer)
        assert perm(request, None) is False


@pytest.mark.django_db
class TestIsAuthenticated:
    """Tests for IsAuthenticated."""

    def test_authenticated_passes(self, customer_factory):
        customer = customer_factory()
        perm = IsAuthenticated()
        request = MockRequest(customer=customer)
        assert perm(request, None) is True

    def test_unauthenticated_fails(self):
        perm = IsAuthenticated()
        request = MockRequest(customer=None)
        assert perm(request, None) is False


@pytest.mark.django_db
class TestHasRoleMixin:
    """Tests for HasRoleMixin helper methods."""

    def test_get_customer_from_request_success(self, customer_factory):
        customer = customer_factory()
        request = MockRequest(customer=customer)

        result = HasRoleMixin.get_customer_from_request(request)
        assert result == customer

    def test_get_customer_from_request_fails_when_missing(self):
        request = MockRequest(customer=None)
        with pytest.raises(ValueError, match="Authentication required"):
            HasRoleMixin.get_customer_from_request(request)

    def test_require_role_passes(self, customer_factory):
        customer = customer_factory()
        RoleService.assign_role(customer, "admin")
        # Should not raise
        HasRoleMixin.require_role(customer, "admin")

    def test_require_role_raises_on_failure(self, customer_factory):
        customer = customer_factory()
        with pytest.raises(InsufficientPrivilegesError):
            HasRoleMixin.require_role(customer, "admin")

    def test_require_permission_passes(self, customer_factory):
        customer = customer_factory()
        RoleService.create_role("tester", permissions={"can_test": True})
        RoleService.assign_role(customer, "tester")
        HasRoleMixin.require_permission(customer, "can_test")

    def test_require_permission_raises(self, customer_factory):
        customer = customer_factory()
        RoleService.create_role("no_perm", permissions={})
        RoleService.assign_role(customer, "no_perm")
        with pytest.raises(PermissionDeniedError):
            HasRoleMixin.require_permission(customer, "need_perm")
