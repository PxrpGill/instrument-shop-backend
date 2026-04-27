"""
Tests for users API endpoints and RBAC protection.
"""
import pytest
from django.urls import reverse
from ninja.testing import TestClient

from instrument_shop.api import api
from apps.users.models import Customer, Role
from apps.users.constants import RoleName
from apps.users.services.customer_service import CustomerService
from apps.users.services.role_service import RoleService
from apps.products.models import Product


@pytest.mark.django_db
class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_registration_creates_customer_and_assigns_customer_role(self, client):
        """Test that registration creates customer and assigns default role."""
        url = "/v1/customers/register"
        response = client.post(
            url,
            json={
                "email": "new@example.com",
                "password": "securepass123",
                "first_name": "New",
                "last_name": "User",
                "phone": "+1234567890",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data

        # Verify customer exists
        customer = Customer.objects.get(email="new@example.com")
        assert customer is not None
        # Default role should be assigned
        assert customer.has_role(RoleName.CUSTOMER) is True

    def test_login_success(self, client, customer_factory):
        """Test successful login."""
        customer = customer_factory(email="login@test.com", password="pass123")
        url = "/v1/customers/login"
        response = client.post(
            url, json={"email": "login@test.com", "password": "pass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access" in data

    def test_login_invalid(self, client):
        """Test login with invalid credentials."""
        url = "/v1/customers/login"
        response = client.post(
            url, json={"email": "wrong@test.com", "password": "wrongpass"}
        )
        assert response.status_code in [400, 401]  # depends on error handling

    def test_get_profile_includes_roles(self, client, customer_factory, auth_headers):
        """Test that /me endpoint returns roles and permissions."""
        customer = customer_factory()
        RoleService.assign_role(customer, RoleName.CUSTOMER)

        headers = auth_headers(customer)

        url = "/v1/customers/me"
        response = client.get(url, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert "permissions" in data
        assert RoleName.CUSTOMER in data["roles"]


@pytest.mark.django_db
class TestRBACPermissions:
    """Tests for role-based access control on endpoints."""

    def test_customer_cannot_create_product(
        self, client, regular_customer, auth_headers
    ):
        """Test that regular customer cannot create product."""
        headers = auth_headers(regular_customer)

        response = client.post(
            "/v1/products/",
            json={"name": "New Product", "price": "99.99", "availability": "in_stock"},
            headers=headers,
        )
        assert response.status_code == 403

    def test_manager_can_create_product(self, client, manager_customer, auth_headers):
        """Test that manager can create product."""
        headers = auth_headers(manager_customer)

        response = client.post(
            "/v1/products/",
            json={
                "name": "Manager Product",
                "price": "150.00",
                "description": "Created by manager",
                "availability": "in_stock",
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Manager Product"
        assert Product.objects.filter(name="Manager Product").exists()

    def test_admin_can_delete_product(
        self, client, admin_customer, product_factory, auth_headers
    ):
        """Test that admin can delete product."""
        product = product_factory(name="ToDelete", price=50)

        headers = auth_headers(admin_customer)
        response = client.delete(f"/v1/products/{product.id}", headers=headers)
        assert response.status_code == 200

    def test_regular_customer_cannot_delete_product(
        self, client, regular_customer, product_factory, auth_headers
    ):
        """Test that regular customer cannot delete product."""
        product = product_factory(name="Protected", price=100)

        headers = auth_headers(regular_customer)
        response = client.delete(f"/v1/products/{product.id}", headers=headers)
        assert response.status_code == 403


@pytest.mark.django_db
class TestRoleManagementAPI:
    """Tests for admin role management endpoints."""

    def test_admin_can_list_roles(self, client, admin_customer, auth_headers):
        """Test admin can list all roles."""
        headers = auth_headers(admin_customer)

        response = client.get("/v1/admin/roles/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # customer, catalog_manager, admin

    def test_manager_cannot_access_admin_endpoints(
        self, client, manager_customer, auth_headers
    ):
        """Test that manager cannot access admin-only endpoints."""
        headers = auth_headers(manager_customer)

        response = client.get("/v1/admin/roles/", headers=headers)
        assert response.status_code == 403

    def test_assign_role_to_customer(
        self, client, admin_customer, customer_factory, auth_headers
    ):
        """Test admin assigning role to customer."""
        target = customer_factory()
        RoleService.create_role("custom_role", permissions={"test": True})

        headers = auth_headers(admin_customer)
        response = client.post(
            f"/v1/admin/customers/{target.id}/roles/",
            json={"role_name": "custom_role"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role_name"] == "custom_role"

        # Verify role was assigned
        target.refresh_from_db()
        assert target.has_role("custom_role") is True

    def test_remove_role_from_customer(
        self, client, admin_customer, customer_factory, auth_headers
    ):
        """Test admin removing role from customer."""
        target = customer_factory()
        RoleService.assign_role(target, RoleName.CATALOG_MANAGER)

        headers = auth_headers(admin_customer)
        response = client.delete(
            f"/v1/admin/customers/{target.id}/roles/{RoleName.CATALOG_MANAGER}/",
            headers=headers,
        )
        assert response.status_code == 200
        target.refresh_from_db()
        assert target.has_role(RoleName.CATALOG_MANAGER) is False

    def test_cannot_assign_nonexistent_role(
        self, client, admin_customer, customer_factory, auth_headers
    ):
        """Test assigning non-existent role returns error."""
        target = customer_factory()

        headers = auth_headers(admin_customer)
        response = client.post(
            f"/v1/admin/customers/{target.id}/roles/",
            json={"role_name": "does_not_exist"},
            headers=headers,
        )
        assert response.status_code in [404, 400]

    def test_customer_cannot_assign_roles(
        self, client, regular_customer, customer_factory, auth_headers
    ):
        """Test that regular customer cannot assign roles."""
        target = customer_factory()

        headers = auth_headers(regular_customer)
        response = client.post(
            f"/v1/admin/customers/{target.id}/roles/",
            json={"role_name": "admin"},
            headers=headers,
        )
        assert response.status_code == 403
