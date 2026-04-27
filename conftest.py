"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
from django.conf import settings

# Configure Django settings for tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instrument_shop.settings')


import django
django.setup()


from ninja.testing import TestClient
from instrument_shop.api import api

from apps.users.models import Customer, Role, CustomerRole
from apps.users.services.role_service import RoleService
from apps.users.services.customer_service import CustomerService


@pytest.fixture
def client():
    """Ninja API test client."""
    return TestClient(api)


@pytest.fixture
def customer_factory():
    """Fixture factory to create test customers."""
    def create_customer(
        email: str = "test@example.com",
        password: str = "testpass123",
        first_name: str = "Test",
        last_name: str = "User",
        phone: str = "+1234567890",
        is_active: bool = True
    ) -> Customer:
        return CustomerService.create_customer(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )
    return create_customer


@pytest.fixture
def role_factory():
    """Fixture factory to create test roles."""
    def create_role(
        name: str = "test_role",
        description: str = "Test role",
        permissions: dict = None
    ) -> Role:
        if permissions is None:
            permissions = {"view_product": True}
        return RoleService.create_role(
            name=name,
            description=description,
            permissions=permissions,
        )
    return create_role


@pytest.fixture
def admin_customer(customer_factory):
    """Create a customer with admin role."""
    customer = customer_factory(email="admin@example.com")
    RoleService.assign_role(customer, 'admin')
    return customer


@pytest.fixture
def manager_customer(customer_factory):
    """Create a customer with manager role."""
    customer = customer_factory(email="manager@example.com")
    RoleService.assign_role(customer, 'manager')
    return customer


@pytest.fixture
def regular_customer(customer_factory):
    """Create a regular customer."""
    customer = customer_factory(email="customer@example.com")
    RoleService.assign_role(customer, 'customer')
    return customer


@pytest.fixture
def setup_default_roles():
    """Ensure default roles exist before tests."""
    return RoleService.initialize_default_roles()
