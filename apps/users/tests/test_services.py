"""
Tests for RoleService.
"""

import pytest
from apps.users.models import Role, Customer, CustomerRole
from apps.users.constants import RoleName, Permission
from apps.users.services.role_service import RoleService
from core.auth.exceptions import (
    RoleNotFoundError,
    CustomerRoleAssignmentError,
    PermissionDeniedError,
    InsufficientPrivilegesError,
)


@pytest.mark.django_db
class TestRoleService:
    """Tests for RoleService static methods."""

    def test_get_role_by_name(self):
        """Test fetching role by name."""
        # Use unique name to avoid conflict
        unique_name = "test_role_by_name"
        Role.objects.create(name=unique_name, permissions={})
        role = RoleService.get_role_by_name(unique_name)
        assert role is not None
        assert role.name == unique_name

    def test_get_role_by_name_not_found(self):
        """Test fetching non-existent role returns None."""
        role = RoleService.get_role_by_name("nonexistent")
        assert role is None

    def test_get_role_by_id(self):
        """Test fetching role by ID."""
        # Use unique name to avoid conflict
        unique_name = "test_role_by_id"
        role = Role.objects.create(name=unique_name, permissions={})
        fetched = RoleService.get_role_by_id(role.id)
        assert fetched == role

    def test_get_all_roles(self):
        """Test listing all roles."""
        # Get initial count (default roles: customer, catalog_manager, admin)
        initial_count = Role.objects.count()

        Role.objects.create(name="test_r1", permissions={})
        Role.objects.create(name="test_r2", permissions={})

        roles = RoleService.get_all_roles()
        # Should have initial + 2 new
        assert len(roles) == initial_count + 2

        names = {r.name for r in roles}
        assert "test_r1" in names
        assert "test_r2" in names

    def test_create_role(self):
        """Test creating a new role."""
        role = RoleService.create_role(
            name="editor", description="Editor role", permissions={"edit": True}
        )
        assert role.name == "editor"
        assert role.description == "Editor role"
        assert role.permissions == {"edit": True}

    def test_create_duplicate_role_fails(self):
        """Test creating duplicate role raises error."""
        Role.objects.create(name="duplicate", permissions={})
        with pytest.raises(CustomerRoleAssignmentError):
            RoleService.create_role(name="duplicate", permissions={})

    def test_update_role(self):
        """Test updating existing role."""
        role = Role.objects.create(name="update_test", permissions={"old": True})
        RoleService.update_role(
            role=role, permissions={"new": False}, description="New description"
        )
        role.refresh_from_db()
        assert role.description == "New description"
        assert role.permissions == {"new": False}

    def test_delete_role(self):
        """Test soft-deleting a role."""
        role = Role.objects.create(name="deletable", permissions={})
        result = RoleService.delete_role(role)
        assert result is True
        role.refresh_from_db()
        assert role.is_active is False

    def test_assign_role(self, customer_factory):
        """Test assigning a role to a customer."""
        customer = customer_factory()
        role = RoleService.create_role("assigned", permissions={})

        customer_role = RoleService.assign_role(customer, "assigned")

        assert customer_role.customer == customer
        assert customer_role.role == role
        assert customer.has_role("assigned") is True

    def test_assign_role_already_assigned(self, customer_factory):
        """Test assigning same role twice raises error."""
        customer = customer_factory()
        RoleService.create_role("dup", permissions={})
        RoleService.assign_role(customer, "dup")

        with pytest.raises(CustomerRoleAssignmentError):
            RoleService.assign_role(customer, "dup")

    def test_assign_nonexistent_role(self, customer_factory):
        """Test assigning non-existent role raises error."""
        customer = customer_factory()
        with pytest.raises(RoleNotFoundError):
            RoleService.assign_role(customer, "does_not_exist")

    def test_remove_role(self, customer_factory):
        """Test removing a role from customer."""
        customer = customer_factory()
        RoleService.create_role("to_remove", permissions={})
        RoleService.assign_role(customer, "to_remove")
        assert customer.has_role("to_remove") is True

        result = RoleService.remove_role(customer, "to_remove")
        assert result is True
        assert customer.has_role("to_remove") is False

    def test_remove_role_not_assigned(self, customer_factory):
        """Test removing non-assigned role returns False."""
        customer = customer_factory()
        RoleService.create_role("not_assigned", permissions={})
        result = RoleService.remove_role(customer, "not_assigned")
        assert result is False

    def test_has_role(self, customer_factory):
        """Test has_role service method."""
        customer = customer_factory()
        RoleService.create_role("test", permissions={})
        RoleService.assign_role(customer, "test")

        assert RoleService.has_role(customer, "test") is True
        assert RoleService.has_role(customer, "other") is False

    def test_has_permission(self, customer_factory):
        """Test has_permission service method."""
        customer = customer_factory()
        RoleService.create_role("perm_test", permissions={"can_do": True})
        RoleService.assign_role(customer, "perm_test")

        assert RoleService.has_permission(customer, "can_do") is True
        assert RoleService.has_permission(customer, "cannot_do") is False

    def test_has_permission_admin_bypasses(self, customer_factory):
        """Test admin role bypasses permission checks."""
        customer = customer_factory()
        RoleService.assign_role(customer, RoleName.ADMIN)

        assert RoleService.has_permission(customer, "anything") is True

    def test_require_role_success(self, customer_factory):
        """Test require_role passes when customer has role."""
        customer = customer_factory()
        RoleService.assign_role(customer, RoleName.CATALOG_MANAGER)
        # Should not raise
        RoleService.require_role(customer, RoleName.CATALOG_MANAGER)

    def test_require_role_failure(self, customer_factory):
        """Test require_role raises when no role."""
        customer = customer_factory()
        with pytest.raises(InsufficientPrivilegesError):
            RoleService.require_role(customer, RoleName.ADMIN)

    def test_require_permission_success(self, customer_factory):
        """Test require_permission passes."""
        customer = customer_factory()
        RoleService.create_role("p_test", permissions={"do_thing": True})
        RoleService.assign_role(customer, "p_test")

        RoleService.require_permission(customer, "do_thing")

    def test_require_permission_admin_bypass(self, customer_factory):
        """Test admin bypasses permission check."""
        customer = customer_factory()
        RoleService.assign_role(customer, RoleName.ADMIN)
        RoleService.require_permission(customer, "impossible_permission")

    def test_require_permission_failure(self, customer_factory):
        """Test require_permission raises when lacking permission."""
        customer = customer_factory()
        RoleService.create_role("no_perm", permissions={})
        RoleService.assign_role(customer, "no_perm")

        with pytest.raises(PermissionDeniedError):
            RoleService.require_permission(customer, "required_perm")

    def test_get_customer_permissions(self, customer_factory):
        """Test get_customer_permissions aggregates from all roles."""
        customer = customer_factory()
        RoleService.create_role("r1", permissions={"p1": True, "p2": False})
        RoleService.create_role("r2", permissions={"p2": True, "p3": True})

        RoleService.assign_role(customer, "r1")
        RoleService.assign_role(customer, "r2")

        perms = RoleService.get_customer_permissions(customer)
        assert perms["p1"] is True
        assert perms["p2"] is True
        assert perms["p3"] is True

    def test_get_customers_with_role(self, customer_factory):
        """Test filtering customers by role."""
        c1 = customer_factory(email="c1@test.com")
        c2 = customer_factory(email="c2@test.com")
        c3 = customer_factory(email="c3@test.com")

        RoleService.create_role("special", permissions={})
        RoleService.assign_role(c1, "special")
        RoleService.assign_role(c2, "special")
        # c3 gets no role

        result = RoleService.get_customers_with_role("special")
        emails = {c.email for c in result}
        assert emails == {"c1@test.com", "c2@test.com"}

    def test_get_customers_with_permission(self, customer_factory):
        """Test filtering customers by permission."""
        RoleService.create_role("perm_role", permissions={"can_edit": True})
        c1 = customer_factory(email="p1@test.com")
        c2 = customer_factory(email="p2@test.com")
        RoleService.assign_role(c1, "perm_role")
        RoleService.assign_role(c2, "perm_role")
        RoleService.create_role("no_perm", permissions={})
        c3 = customer_factory(email="p3@test.com")
        RoleService.assign_role(c3, "no_perm")

        result = RoleService.get_customers_with_permission("can_edit")
        emails = {c.email for c in result}
        assert emails == {"p1@test.com", "p2@test.com"}

    def test_initialize_default_roles(self):
        """Test creation of default system roles."""
        roles = RoleService.initialize_default_roles()

        assert RoleName.CUSTOMER in roles
        assert RoleName.CATALOG_MANAGER in roles
        assert RoleName.ADMIN in roles

        assert roles[RoleName.CUSTOMER].has_permission(Permission.VIEW_PRODUCT) is True
        assert roles[RoleName.ADMIN].has_permission(Permission.WILDCARD) is True

    def test_get_customer_roles(self, customer_factory):
        """Test getting all roles for a customer."""
        customer = customer_factory()
        RoleService.create_role("r1", permissions={})
        RoleService.create_role("r2", permissions={})
        RoleService.assign_role(customer, "r1")
        RoleService.assign_role(customer, "r2")

        roles = RoleService.get_customer_roles(customer)
        role_names = {r.name for r in roles}
        assert role_names == {"r1", "r2"}
