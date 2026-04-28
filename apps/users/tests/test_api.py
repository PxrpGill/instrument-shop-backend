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


@pytest.mark.django_db
class TestGetCustomerFromRequest:
    """Tests for get_customer_from_request function."""

    def test_no_auth_header(self, client):
        """Test get_customer_from_request with no Authorization header."""
        # Directly test the function by calling an endpoint without auth
        response = client.get("/v1/customers/me")
        assert response.status_code in [401, 403, 422]

    def test_invalid_token_format(self, client):
        """Test get_customer_from_request with invalid token format."""
        headers = {"Authorization": "InvalidFormat token"}
        response = client.get("/v1/customers/me", headers=headers)
        assert response.status_code in [401, 403, 422]

    def test_expired_token(self, client, customer_factory):
        """Test get_customer_from_request with expired token."""
        from rest_framework_simplejwt.tokens import AccessToken
        from datetime import timedelta
        
        customer = customer_factory()
        # Create an expired token
        token = AccessToken()
        token["user_id"] = str(customer.id)
        token.set_exp(lifetime=timedelta(seconds=-1))
        
        headers = {"Authorization": f"Bearer {str(token)}"}
        response = client.get("/v1/customers/me", headers=headers)
        assert response.status_code in [401, 403]


@pytest.mark.django_db
class TestTokenRefreshEndpoint:
    """Tests for token refresh endpoint."""

    def test_refresh_success(self, client, customer_factory):
        """Test successful token refresh."""
        customer = customer_factory()
        tokens = CustomerService.generate_tokens(customer)
        
        response = client.post(
            "/v1/customers/refresh",
            json={"refresh": tokens["refresh"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token."""
        response = client.post(
            "/v1/customers/refresh",
            json={"refresh": "invalid_token"}
        )
        assert response.status_code == 401

    def test_refresh_missing_user_id(self, client):
        """Test refresh with token missing user_id."""
        from rest_framework_simplejwt.tokens import RefreshToken
        
        # Create a refresh token without user_id
        refresh = RefreshToken()
        # Don't set user_id
        
        response = client.post(
            "/v1/customers/refresh",
            json={"refresh": str(refresh)}
        )
        assert response.status_code == 401

    def test_refresh_inactive_user(self, client, customer_factory):
        """Test refresh with inactive user."""
        customer = customer_factory()
        tokens = CustomerService.generate_tokens(customer)
        
        # Deactivate user
        customer.is_active = False
        customer.save()
        
        response = client.post(
            "/v1/customers/refresh",
            json={"refresh": tokens["refresh"]}
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestUpdateProfileEndpoint:
    """Tests for update profile endpoint."""

    def test_update_profile_success(self, client, customer_factory, auth_headers):
        """Test successful profile update."""
        customer = customer_factory()
        headers = auth_headers(customer)
        
        response = client.patch(
            "/v1/customers/me",
            json={
                "first_name": "Updated",
                "last_name": "Name",
                "phone": "+9876543210",
                "address": "New Address"
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["phone"] == "+9876543210"

    def test_update_profile_no_auth(self, client):
        """Test update profile without auth."""
        response = client.patch(
            "/v1/customers/me",
            json={"first_name": "Should", "last_name": "Fail"}
        )
        assert response.status_code in [401, 403, 422]


@pytest.mark.django_db
class TestChangePasswordEndpoint:
    """Tests for change password endpoint."""

    def test_change_password_success(self, client, customer_factory, auth_headers):
        """Test successful password change."""
        customer = customer_factory(email="changepass2@example.com", password="oldpass123")
        headers = auth_headers(customer)
        
        response = client.post(
            "/v1/customers/change-password",
            json={
                "old_password": "oldpass123",
                "new_password": "newpass456"
            },
            headers=headers
        )
        assert response.status_code == 200
        
        # Verify can login with new password
        login_response = client.post(
            "/v1/customers/login",
            json={
                "email": "changepass2@example.com",
                "password": "newpass456"
            }
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_old(self, client, customer_factory, auth_headers):
        """Test change password with wrong old password."""
        customer = customer_factory(email="wrongold2@example.com", password="correctpass")
        headers = auth_headers(customer)
        
        response = client.post(
            "/v1/customers/change-password",
            json={
                "old_password": "wrongpass",
                "new_password": "newpass456"
            },
            headers=headers
        )
        assert response.status_code == 400

    def test_change_password_no_auth(self, client):
        """Test change password without auth."""
        response = client.post(
            "/v1/customers/change-password",
            json={
                "old_password": "oldpass",
                "new_password": "newpass"
            }
        )
        assert response.status_code in [401, 403, 422]

    def test_register_duplicate_email(self, client, customer_factory):
        """Test registration with duplicate email (covers controllers.py:68)."""
        customer_factory(email="duplicate@example.com")
        
        response = client.post(
            "/v1/customers/register",
            json={
                "email": "duplicate@example.com",
                "password": "testpass123",
                "first_name": "Duplicate",
                "last_name": "User",
                "phone": "+1234567890",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "already" in str(data).lower() or "уже" in str(data).lower()

    def test_token_without_user_id(self, client):
        """Test access with token missing user_id (covers controllers.py:49)."""
        from rest_framework_simplejwt.tokens import AccessToken
        
        # Create token without user_id
        token = AccessToken()
        # Don't set user_id
        
        headers = {"Authorization": f"Bearer {str(token)}"}
        response = client.get("/v1/customers/me", headers=headers)
        assert response.status_code == 401
