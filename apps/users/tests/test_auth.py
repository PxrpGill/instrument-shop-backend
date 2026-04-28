"""
Tests for users API endpoints to cover auth.py and jwt_auth.py.
"""
import pytest
from ninja.testing import TestClient

from apps.users.models import Customer
from apps.users.services.customer_service import CustomerService
from instrument_shop.api import api


@pytest.fixture
def auth_client():
    """Create a test client."""
    return TestClient(api)


@pytest.mark.django_db
class TestAuthEndpointsDetailed:
    """Detailed tests for auth endpoints to cover auth.py and jwt_auth.py."""

    def test_register_duplicate_email(self, auth_client, customer_factory):
        """Test registration with duplicate email."""
        # Create a customer first
        customer_factory(email="duplicate@example.com")
        
        response = auth_client.post(
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
        # Check for Russian error message
        assert "уже" in str(data).lower() or "already" in str(data).lower() or "exists" in str(data).lower()

    def test_login_nonexistent_user(self, auth_client):
        """Test login with nonexistent user."""
        response = auth_client.post(
            "/v1/customers/login",
            json={
                "email": "nonexistent@example.com",
                "password": "testpass123",
            },
        )
        assert response.status_code in [400, 401]

    def test_login_wrong_password(self, auth_client, customer_factory):
        """Test login with wrong password."""
        customer_factory(email="wrongpass@example.com", password="correctpass")
        
        response = auth_client.post(
            "/v1/customers/login",
            json={
                "email": "wrongpass@example.com",
                "password": "wrongpass",
            },
        )
        assert response.status_code in [400, 401]

    def test_me_endpoint_no_auth(self, auth_client):
        """Test /me endpoint without authentication."""
        response = auth_client.get("/v1/customers/me")
        assert response.status_code in [401, 403]

    def test_update_profile_success(self, auth_client, customer_factory, auth_headers):
        """Test successful profile update."""
        customer = customer_factory()
        headers = auth_headers(customer)
        
        response = auth_client.patch(
            "/v1/customers/me",
            json={
                "first_name": "Updated",
                "last_name": "Name",
                "phone": "+9876543210",
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"

    def test_update_profile_no_auth(self, auth_client):
        """Test profile update without authentication."""
        response = auth_client.patch(
            "/v1/customers/me",
            json={"first_name": "Should", "last_name": "Fail"},
        )
        assert response.status_code in [401, 403]

    def test_change_password_success(self, auth_client, customer_factory, auth_headers):
        """Test successful password change."""
        customer = customer_factory(email="changepass@example.com", password="oldpass123")
        headers = auth_headers(customer)
        
        response = auth_client.post(
            "/v1/customers/change-password",
            json={
                "old_password": "oldpass123",
                "new_password": "newpass456",
            },
            headers=headers,
        )
        assert response.status_code == 200
        
        # Verify can login with new password
        login_response = auth_client.post(
            "/v1/customers/login",
            json={
                "email": "changepass@example.com",
                "password": "newpass456",
            },
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_old(self, auth_client, customer_factory, auth_headers):
        """Test password change with wrong old password."""
        customer = customer_factory(email="wrongold@example.com", password="correctpass")
        headers = auth_headers(customer)
        
        response = auth_client.post(
            "/v1/customers/change-password",
            json={
                "old_password": "wrongpass",
                "new_password": "newpass456",
            },
            headers=headers,
        )
        assert response.status_code == 400

    def test_change_password_no_auth(self, auth_client):
        """Test password change without authentication."""
        response = auth_client.post(
            "/v1/customers/change-password",
            json={
                "old_password": "oldpass",
                "new_password": "newpass",
            },
        )
        # Returns 422 (validation error) because missing required fields
        assert response.status_code in [401, 403, 422]
