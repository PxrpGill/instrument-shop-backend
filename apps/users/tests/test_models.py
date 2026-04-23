"""
Tests for users models (Role, Customer, CustomerRole).
"""
import pytest
from django.core.exceptions import ValidationError
from apps.users.models import Customer, Role, CustomerRole
from apps.users.services.customer_service import CustomerService
from apps.users.services.role_service import RoleService


@pytest.mark.django_db
class TestRoleModel:
    """Tests for Role model."""

    def test_create_role(self):
        """Test creating a role."""
        role = RoleService.create_role(
            name="tester",
            description="Test role",
            permissions={"view_product": True, "edit_product": False}
        )
        assert role.name == "tester"
        assert role.description == "Test role"
        assert role.permissions == {"view_product": True, "edit_product": False}
        assert role.is_active is True

    def test_role_str_representation(self):
        """Test string representation."""
        role = Role.objects.create(name="admin", permissions={})
        assert str(role) == "admin"

    def test_role_has_permission(self):
        """Test has_permission method."""
        role = Role.objects.create(
            name="manager",
            permissions={"create_product": True, "edit_product": True}
        )
        assert role.has_permission("create_product") is True
        assert role.has_permission("delete_product") is False

    def test_role_wildcard_permission(self):
        """Test wildcard permission (*) grants all."""
        role = Role.objects.create(
            name="admin",
            permissions={"*": True}
        )
        assert role.has_permission("anything") is True
        assert role.has_permission("destroy_system") is True

    def test_role_unique_name(self):
        """Test that role names must be unique."""
        Role.objects.create(name="unique_role", permissions={})
        with pytest.raises(Exception):  # Should be IntegrityError but depends on DB
            Role.objects.create(name="unique_role", permissions={})

    def test_get_all_permissions(self):
        """Test get_all_permissions returns a copy."""
        perms = {"view": True, "edit": False}
        role = Role.objects.create(name="test", permissions=perms)
        result = role.get_all_permissions()
        assert result == perms
        # Ensure it's a copy
        result["new"] = True
        assert "new" not in role.permissions


@pytest.mark.django_db
class TestCustomerModel:
    """Tests for Customer model."""

    def test_create_customer(self, customer_factory):
        """Test creating a customer."""
        customer = customer_factory(email="new@example.com")
        assert Customer.objects.count() == 1
        assert customer.email == "new@example.com"
        assert customer.is_active is True

    def test_customer_str(self):
        """Test string representation."""
        customer = Customer.objects.create(
            email="str@test.com",
            password_hash="hashed"
        )
        assert str(customer) == "str@test.com"

    def test_get_full_name(self):
        """Test get_full_name method."""
        customer = Customer.objects.create(
            email="fullname@test.com",
            password_hash="hashed",
            first_name="John",
            last_name="Doe"
        )
        assert customer.get_full_name() == "John Doe"

        customer.first_name = ""
        assert customer.get_full_name() == "Doe"

        customer.last_name = ""
        assert customer.get_full_name() == ""

    def test_update_last_login(self):
        """Test updating last_login timestamp."""
        customer = Customer.objects.create(
            email="login@test.com",
            password_hash="hashed"
        )
        assert customer.last_login is None
        customer.update_last_login()
        assert customer.last_login is not None


@pytest.mark.django_db
class TestRBACIntegration:
    """Integration tests for RBAC system."""

    def test_customer_has_role(self, customer_factory):
        """Test customer.has_role() method."""
        customer = customer_factory()
        role = RoleService.create_role("viewer", permissions={"view": True})
        RoleService.assign_role(customer, "viewer")

        assert customer.has_role("viewer") is True
        assert customer.has_role("nonexistent") is False

    def test_customer_has_permission(self, customer_factory):
        """Test customer.has_permission() method."""
        customer = customer_factory()
        RoleService.create_role(
            "editor",
            permissions={"edit_product": True, "view_product": False}
        )
        RoleService.assign_role(customer, "editor")

        assert customer.has_permission("edit_product") is True
        assert customer.has_permission("view_product") is False

    def test_customer_has_permission_admin_wildcard(self, customer_factory):
        """Test admin wildcard grants all permissions."""
        customer = customer_factory()
        RoleService.assign_role(customer, "admin")

        assert customer.has_permission("any_permission") is True
        assert customer.has_permission("system_override") is True

    def test_multiple_roles_permissions(self, customer_factory):
        """Test permissions aggregate from multiple roles."""
        customer = customer_factory()
        RoleService.create_role("role1", permissions={"perm1": True})
        RoleService.create_role("role2", permissions={"perm2": True})

        RoleService.assign_role(customer, "role1")
        RoleService.assign_role(customer, "role2")

        assert customer.has_permission("perm1") is True
        assert customer.has_permission("perm2") is True
        assert customer.has_permission("perm3") is False

    def test_customer_get_roles(self, customer_factory):
        """Test get_roles method."""
        customer = customer_factory()
        RoleService.create_role("role_a", permissions={})
        RoleService.create_role("role_b", permissions={})

        RoleService.assign_role(customer, "role_a")
        RoleService.assign_role(customer, "role_b")

        roles = customer.get_roles()
        role_names = {r.name for r in roles}
        assert role_names == {"role_a", "role_b"}

    def test_customer_get_permissions(self, customer_factory):
        """Test get_permissions method aggregates correctly."""
        customer = customer_factory()
        RoleService.create_role("r1", permissions={"p1": True, "p2": False})
        RoleService.create_role("r2", permissions={"p2": True, "p3": True})

        RoleService.assign_role(customer, "r1")
        RoleService.assign_role(customer, "r2")

        perms = customer.get_permissions()
        assert perms["p1"] is True
        assert perms["p2"] is True
        assert perms["p3"] is True

    def test_customer_get_permissions_true_is_not_overridden_by_false(self, customer_factory):
        """Test that any granting role keeps permission enabled."""
        customer = customer_factory()
        RoleService.create_role("grant_role", permissions={"manage_orders": True})
        RoleService.create_role("deny_role", permissions={"manage_orders": False})

        RoleService.assign_role(customer, "grant_role")
        RoleService.assign_role(customer, "deny_role")

        perms = customer.get_permissions()
        assert perms["manage_orders"] is True
