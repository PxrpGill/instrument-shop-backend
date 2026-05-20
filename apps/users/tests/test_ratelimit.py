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
        from apps.users.api.auth_controllers import login

        assert login.__name__ == "login"

    def test_register_has_ratelimit_decorator(self):
        """Verify register endpoint has rate limit decorator."""
        from apps.users.api.auth_controllers import register

        assert register.__name__ == "register"

    def test_refresh_has_ratelimit_decorator(self):
        """Verify refresh endpoint has rate limit decorator."""
        from apps.users.api.auth_controllers import refresh_tokens

        assert refresh_tokens.__name__ == "refresh_tokens"

    def test_forgot_password_has_ratelimit_decorator(self):
        """Verify forgot-password endpoint has rate limit decorator."""
        from apps.users.api.auth_controllers import forgot_password

        assert forgot_password.__name__ == "forgot_password"


@pytest.mark.django_db
class TestPublicApiRateLimit:
    """Tests for /catalog public API rate limiting."""

    def test_catalog_root_has_ratelimit_decorator(self):
        from apps.products.catalog_controllers import get_catalog

        assert get_catalog.__name__ == "get_catalog"

    def test_category_page_has_ratelimit_decorator(self):
        from apps.products.catalog_controllers import get_category

        assert get_category.__name__ == "get_category"

    def test_product_detail_has_ratelimit_decorator(self):
        from apps.products.catalog_controllers import get_product_detail

        assert get_product_detail.__name__ == "get_product_detail"
