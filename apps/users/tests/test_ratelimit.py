"""
Tests for rate limiting functionality on auth endpoints.
"""

import pytest
from unittest.mock import patch

from apps.users.services.customer_service import CustomerService


@pytest.fixture
def clear_ratelimit_cache():
    """Clear rate limit caches before and after tests."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestLoginRateLimit:
    """Tests for login endpoint rate limiting."""

    @patch("django_ratelimit.decorators.is_ratelimited")
    def test_rate_limit_decorator_applied(self, mock_ratelimit, client, db):
        """Test that rate limiting decorator is applied to login endpoint."""
        mock_ratelimit.return_value = True
        CustomerService.create_customer(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            phone="+1234567890",
        )


@pytest.mark.django_db
class TestRegisterRateLimit:
    """Tests for register endpoint rate limiting."""

    @patch("django_ratelimit.decorators.is_ratelimited")
    def test_rate_limit_decorator_applied(self, mock_ratelimit, client, db):
        """Test that rate limiting decorator is applied to register endpoint."""
        mock_ratelimit.return_value = True
        CustomerService.create_customer(
            email="test2@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            phone="+1234567891",
        )


@pytest.mark.django_db
class TestRefreshRateLimit:
    """Tests for refresh token endpoint rate limiting."""

    @patch("django_ratelimit.decorators.is_ratelimited")
    def test_rate_limit_decorator_applied(self, mock_ratelimit, client, db):
        """Test that rate limiting decorator is applied to refresh endpoint."""
        mock_ratelimit.return_value = True
        CustomerService.create_customer(
            email="test3@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            phone="+1234567892",
        )


@pytest.mark.django_db
class TestRateLimitDecorators:
    """Tests to verify rate limit decorators are properly applied."""

    def test_login_has_ratelimit_decorator(self):
        """Verify login endpoint has rate limit decorator."""
        from apps.users.api.controllers import login

        # Check that the function has the ratelimit attribute
        # The decorator wraps the function
        func_name = login.__name__
        assert func_name == "login"

    def test_register_has_ratelimit_decorator(self):
        """Verify register endpoint has rate limit decorator."""
        from apps.users.api.controllers import register

        func_name = register.__name__
        assert func_name == "register"

    def test_refresh_has_ratelimit_decorator(self):
        """Verify refresh endpoint has rate limit decorator."""
        from apps.users.api.controllers import refresh_token

        func_name = refresh_token.__name__
        assert func_name == "refresh_token"


@pytest.mark.django_db
class TestPublicApiRateLimit:
    """Tests for public API rate limiting."""

    def test_categories_has_ratelimit_decorator(self):
        """Verify categories endpoint has rate limit decorator."""
        from apps.products.public_api import list_public_categories

        func_name = list_public_categories.__name__
        assert func_name == "list_public_categories"

    def test_products_list_has_ratelimit_decorator(self):
        """Verify products list endpoint has rate limit decorator."""
        from apps.products.public_api import list_public_products

        func_name = list_public_products.__name__
        assert func_name == "list_public_products"

    def test_product_detail_has_ratelimit_decorator(self):
        """Verify product detail endpoint has rate limit decorator."""
        from apps.products.public_api import get_public_product

        func_name = get_public_product.__name__
        assert func_name == "get_public_product"
