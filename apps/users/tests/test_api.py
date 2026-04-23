"""
Tests for users API endpoints and RBAC protection.
"""
import pytest
from django.urls import reverse
from ninja.testing import TestClient
from rest_framework_simplejwt.tokens import RefreshToken

from instrument_shop.api import api
from apps.users.models import Customer, Role
from apps.users.services.role_service import RoleService


@pytest.mark.django_db
class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_registration_creates_customer_and_assigns_customer_role(self, client):
        """Test that registration creates customer and assigns default role."""
        url = '/api/v1/customers/register'
        response = client.post(url, {
            "email": "new@example.com",
            "password": "securepass123",
            "first_name": "New",
            "last_name": "User"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data

        # Verify customer exists
        customer = Customer.objects.get(email="new@example.com")
        assert customer is not None
        # Default role should be assigned
        assert customer.has_role("customer") is True

    def test_login_success(self, client, customer_factory):
        """Test successful login."""
        customer = customer_factory(email="login@test.com", password="pass123")
        url = '/api/v1/customers/login'
        response = client.post(url, {
            "email": "login@test.com",
            "password": "pass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access" in data

    def test_login_invalid(self, client):
        """Test login with invalid credentials."""
        url = '/api/v1/customers/login'
        response = client.post(url, {
            "email": "wrong@test.com",
            "password": "wrongpass"
        })
        assert response.status_code == 400  # or 401 depending on error handling

    def test_get_profile_includes_roles(self, client, customer_factory):
        """Test that /me endpoint returns roles and permissions."""
        customer = customer_factory()
        RoleService.assign_role(customer, "customer")

        # Generate token
        tokens = RefreshToken.for_user(customer)
        access = str(tokens.access_token)

        url = '/api/v1/customers/me'
        response = client.get(url, HTTP_AUTHORIZATION=f'Bearer {access}')
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert "permissions" in data
        assert "customer" in data["roles"]


@pytest.mark.django_db
class TestRBACPermissions:
    """Tests for role-based access control on endpoints."""

    def test_customer_cannot_create_product(self, client, regular_customer):
        """Test that regular customer cannot create product."""
        tokens = RefreshToken.for_user(regular_customer)
        access = str(tokens.access_token)

        url = '/api/v1/products/'
        response = client.post(url, {
            "name": "Test Product",
            "price": "100.00"
        }, HTTP_AUTHORIZATION=f'Bearer {access}')

        # Should be forbidden (403)
        assert response.status_code == 403

    def test_manager_can_create_product(self, client, manager_customer):
        """Test that manager can create product."""
        tokens = RefreshToken.for_user(manager_customer)
        access = str(tokens.access_token)

        url = '/api/v1/products/'
        response = client.post(url, {
            "name": "Manager Product",
            "price": "200.00"
        }, HTTP_AUTHORIZATION=f'Bearer {access}')

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Manager Product"

    def test_admin_can_delete_product(self, client, admin_customer, product_factory):
        """Test that admin can delete product."""
        # Create a product first
        product = product_factory(name="ToDelete", price=50)

        tokens = RefreshToken.for_user(admin_customer)
        access = str(tokens.access_token)

        url = f'/api/v1/products/{product.id}/'
        response = client.delete(url, HTTP_AUTHORIZATION=f'Bearer {access}')
        assert response.status_code == 200

    def test_regular_customer_cannot_delete_product(self, client, regular_customer, product_factory):
        """Test that regular customer cannot delete product."""
        product = product_factory(name="Protected", price=100)

        tokens = RefreshToken.for_user(regular_customer)
        access = str(tokens.access_token)

        url = f'/api/v1/products/{product.id}/'
        response = client.delete(url, HTTP_AUTHORIZATION=f'Bearer {access}')
        assert response.status_code == 403


@pytest.mark.django_db
class TestRoleManagementAPI:
    """Tests for admin role management endpoints."""

    def test_admin_can_list_roles(self, client, admin_customer):
        """Test admin can list all roles."""
        tokens = RefreshToken.for_user(admin_customer)
        access = str(tokens.access_token)

        url = '/api/v1/admin/roles/'
        response = client.get(url, HTTP_AUTHORIZATION=f'Bearer {access}')
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # customer, manager, admin

    def test_manager_cannot_access_admin_endpoints(self, client, manager_customer):
        """Test that manager cannot access admin-only endpoints."""
        tokens = RefreshToken.for_user(manager_customer)
        access = str(tokens.access_token)

        url = '/api/v1/admin/roles/'
        response = client.get(url, HTTP_AUTHORIZATION=f'Bearer {access}')
        assert response.status_code == 403

    def test_assign_role_to_customer(self, client, admin_customer, customer_factory):
        """Test admin assigning role to customer."""
        target = customer_factory()
        RoleService.create_role("custom_role", permissions={"test": True})

        tokens = RefreshToken.for_user(admin_customer)
        access = str(tokens.access_token)

        url = f'/api/v1/admin/customers/{target.id}/roles/'
        response = client.post(url, {
            "role_name": "custom_role"
        }, HTTP_AUTHORIZATION=f'Bearer {access}')
        assert response.status_code == 200
        data = response.json()
        assert data["role_name"] == "custom_role"

        # Verify role was assigned
        assert target.has_role("custom_role") is True

    def test_remove_role_from_customer(self, client, admin_customer, customer_factory):
        """Test admin removing role from customer."""
        target = customer_factory()
        RoleService.assign_role(target, "manager")

        tokens = RefreshToken.for_user(admin_customer)
        access = str(tokens.access_token)

        url = f'/api/v1/admin/customers/{target.id}/roles/manager/'
        response = client.delete(url, HTTP_AUTHORIZATION=f'Bearer {access}')
        assert response.status_code == 200
        assert target.has_role("manager") is False

    def test_cannot_assign_nonexistent_role(self, client, admin_customer, customer_factory):
        """Test assigning non-existent role returns error."""
        target = customer_factory()

        tokens = RefreshToken.for_user(admin_customer)
        access = str(tokens.access_token)

        url = f'/api/v1/admin/customers/{target.id}/roles/'
        response = client.post(url, {
            "role_name": "does_not_exist"
        }, HTTP_AUTHORIZATION=f'Bearer {access}')
        assert response.status_code == 404  # or 400

    def test_customer_cannot_assign_roles(self, client, regular_customer, customer_factory):
        """Test that regular customer cannot assign roles."""
        target = customer_factory()

        tokens = RefreshToken.for_user(regular_customer)
        access = str(tokens.access_token)

        url = f'/api/v1/admin/customers/{target.id}/roles/'
        response = client.post(url, {
            "role_name": "admin"
        }, HTTP_AUTHORIZATION=f'Bearer {access}')
        assert response.status_code == 403
