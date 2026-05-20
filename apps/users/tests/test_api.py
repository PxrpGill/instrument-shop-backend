"""RBAC и role-management тесты на эндпоинтах вне /api/auth.

Тесты под новый /api/auth/ контракт живут в test_auth_endpoints.py.
"""

import pytest

from apps.products.models import Product
from apps.users.constants import RoleName
from apps.users.services.role_service import RoleService


@pytest.mark.django_db
class TestRBACPermissions:
    """Tests for role-based access control on existing /v1/ endpoints."""

    def test_customer_cannot_create_product(
        self, client, regular_customer, auth_headers
    ):
        headers = auth_headers(regular_customer)
        response = client.post(
            "/v1/products/",
            json={"name": "New Product", "price": "99.99", "availability": "in_stock"},
            headers=headers,
        )
        assert response.status_code == 403

    def test_manager_can_create_product(self, client, manager_customer, auth_headers):
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
        assert Product.objects.filter(name="Manager Product").exists()

    def test_admin_can_delete_product(
        self, client, admin_customer, product_factory, auth_headers
    ):
        product = product_factory(name="ToDelete", price=50)
        headers = auth_headers(admin_customer)
        response = client.delete(f"/v1/products/{product.id}", headers=headers)
        assert response.status_code == 200

    def test_regular_customer_cannot_delete_product(
        self, client, regular_customer, product_factory, auth_headers
    ):
        product = product_factory(name="Protected", price=100)
        headers = auth_headers(regular_customer)
        response = client.delete(f"/v1/products/{product.id}", headers=headers)
        assert response.status_code == 403


@pytest.mark.django_db
class TestRoleManagementAPI:
    """Admin role management endpoints (/v1/admin/...) — не покрываются контрактом."""

    def test_admin_can_list_roles(self, client, admin_customer, auth_headers):
        headers = auth_headers(admin_customer)
        response = client.get("/v1/admin/roles/", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) >= 3

    def test_manager_cannot_access_admin_endpoints(
        self, client, manager_customer, auth_headers
    ):
        headers = auth_headers(manager_customer)
        response = client.get("/v1/admin/roles/", headers=headers)
        assert response.status_code == 403

    def test_assign_role_to_customer(
        self, client, admin_customer, customer_factory, auth_headers
    ):
        target = customer_factory()
        RoleService.create_role("custom_role", permissions={"test": True})

        headers = auth_headers(admin_customer)
        response = client.post(
            f"/v1/admin/customers/{target.id}/roles/",
            json={"role_name": "custom_role"},
            headers=headers,
        )
        assert response.status_code == 200
        target.refresh_from_db()
        assert target.has_role("custom_role")

    def test_remove_role_from_customer(
        self, client, admin_customer, customer_factory, auth_headers
    ):
        target = customer_factory()
        RoleService.assign_role(target, RoleName.CATALOG_MANAGER)

        headers = auth_headers(admin_customer)
        response = client.delete(
            f"/v1/admin/customers/{target.id}/roles/{RoleName.CATALOG_MANAGER}/",
            headers=headers,
        )
        assert response.status_code == 200
        target.refresh_from_db()
        assert not target.has_role(RoleName.CATALOG_MANAGER)
