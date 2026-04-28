"""
Tests for role controllers (admin endpoints).
"""
import pytest
from ninja.testing import TestClient
from django.urls import reverse

from apps.users.models import Customer, Role
from apps.users.constants import RoleName
from apps.users.services.role_service import RoleService
from apps.users.services.customer_service import CustomerService
from instrument_shop.api import api


@pytest.fixture
def admin_client():
    """Create a test client."""
    return TestClient(api)


@pytest.mark.django_db
class TestRoleControllersAdmin:
    """Tests for admin role management endpoints."""

    def test_get_role_success(self, admin_client, admin_customer, auth_headers):
        """Test admin can get a specific role."""
        headers = auth_headers(admin_customer)
        
        # Get an existing role
        role = Role.objects.filter(is_active=True).first()
        assert role is not None
        
        response = admin_client.get(f"/v1/admin/roles/{role.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == role.id
        assert data["name"] == role.name

    def test_get_role_nonexistent(self, admin_client, admin_customer, auth_headers):
        """Test admin gets 404 for nonexistent role."""
        headers = auth_headers(admin_customer)
        
        response = admin_client.get("/v1/admin/roles/99999", headers=headers)
        assert response.status_code == 404

    def test_create_role_success(self, admin_client, admin_customer, auth_headers):
        """Test admin can create a new role."""
        headers = auth_headers(admin_customer)
        
        response = admin_client.post(
            "/v1/admin/roles/",
            json={
                "name": "test_new_role",
                "description": "Test role",
                "permissions": {"view_product": True}
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_new_role"
        assert data["description"] == "Test role"
        
        # Verify in database
        assert Role.objects.filter(name="test_new_role").exists()

    def test_create_duplicate_role_fails(self, admin_client, admin_customer, auth_headers):
        """Test creating duplicate role fails."""
        headers = auth_headers(admin_customer)
        
        # Try to create role with existing name
        response = admin_client.post(
            "/v1/admin/roles/",
            json={
                "name": RoleName.ADMIN,  # Already exists
                "permissions": {}
            },
            headers=headers,
        )
        assert response.status_code in [400, 409, 422]

    def test_update_role_success(self, admin_client, admin_customer, auth_headers):
        """Test admin can update a role."""
        headers = auth_headers(admin_customer)
        
        # Create a test role first
        role = RoleService.create_role(
            name="role_to_update",
            description="Original",
            permissions={"view_product": True}
        )
        
        response = admin_client.put(
            f"/v1/admin/roles/{role.id}",
            json={
                "description": "Updated description",
                "permissions": {"view_product": True, "edit_product": False}
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        
        # Verify in database
        role.refresh_from_db()
        assert role.description == "Updated description"

    def test_delete_role_success(self, admin_client, admin_customer, auth_headers):
        """Test admin can delete (deactivate) a role."""
        headers = auth_headers(admin_customer)
        
        # Create a test role first
        role = RoleService.create_role(
            name="role_to_delete",
            description="To be deleted",
            permissions={}
        )
        
        response = admin_client.delete(f"/v1/admin/roles/{role.id}", headers=headers)
        assert response.status_code == 200
        
        # Verify role is deactivated, not deleted from DB
        role.refresh_from_db()
        assert role.is_active is False

    def test_delete_system_role_fails(self, admin_client, admin_customer, auth_headers):
        """Test cannot delete system roles (admin, customer, catalog_manager)."""
        headers = auth_headers(admin_customer)
        
        # Get admin role
        admin_role = Role.objects.get(name=RoleName.ADMIN)
        
        response = admin_client.delete(f"/v1/admin/roles/{admin_role.id}", headers=headers)
        assert response.status_code in [400, 403]
        data = response.json()
        assert "system" in str(data).lower() or "нельзя" in str(data).lower()

    def test_delete_nonexistent_role(self, admin_client, admin_customer, auth_headers):
        """Test deleting nonexistent role returns 404."""
        headers = auth_headers(admin_customer)
        
        response = admin_client.delete("/v1/admin/roles/99999", headers=headers)
        assert response.status_code == 404

    def test_update_nonexistent_role(self, admin_client, admin_customer, auth_headers):
        """Test updating nonexistent role returns 404 (covers line 97)."""
        headers = auth_headers(admin_customer)
        
        response = admin_client.put(
            "/v1/admin/roles/99999",
            json={
                "description": "Updated description",
                "permissions": {"view_product": True}
            },
            headers=headers,
        )
        assert response.status_code == 404

    def test_manager_cannot_access_role_endpoints(self, admin_client, manager_customer, auth_headers):
        """Test that manager cannot access admin role endpoints."""
        headers = auth_headers(manager_customer)
        
        # Try to list roles - should fail
        response = admin_client.get("/v1/admin/roles/", headers=headers)
        assert response.status_code in [403, 404]

    def test_customer_cannot_access_role_endpoints(self, admin_client, regular_customer, auth_headers):
        """Test that regular customer cannot access admin role endpoints."""
        headers = auth_headers(regular_customer)
        
        response = admin_client.get("/v1/admin/roles/", headers=headers)
        assert response.status_code in [403, 404]

    def test_get_customer_roles_admin(self, admin_client, admin_customer, regular_customer, auth_headers):
        """Test admin can view customer's roles."""
        headers = auth_headers(admin_customer)
        
        # Customer should already have a role assigned (from fixture)
        response = admin_client.get(f"/v1/admin/customers/{regular_customer.id}/roles/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_assign_role_to_customer_by_admin(self, admin_client, admin_customer, regular_customer, auth_headers):
        """Test admin can assign role to customer."""
        headers = auth_headers(admin_customer)
        
        response = admin_client.post(
            f"/v1/admin/customers/{regular_customer.id}/roles/",
            json={"role_name": RoleName.CATALOG_MANAGER},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role_name"] == RoleName.CATALOG_MANAGER
        
        # Verify in database
        assert regular_customer.has_role(RoleName.CATALOG_MANAGER)

    def test_remove_role_from_customer_by_admin(self, admin_client, admin_customer, regular_customer, auth_headers):
        """Test admin can remove role from customer."""
        headers = auth_headers(admin_customer)
        
        # First assign a role
        RoleService.assign_role(regular_customer, RoleName.CATALOG_MANAGER)
        assert regular_customer.has_role(RoleName.CATALOG_MANAGER)
        
        # Now remove it
        response = admin_client.delete(
            f"/v1/admin/customers/{regular_customer.id}/roles/{RoleName.CATALOG_MANAGER}/",
            headers=headers,
        )
        assert response.status_code == 200
        
        # Verify role removed
        regular_customer.refresh_from_db()
        assert not regular_customer.has_role(RoleName.CATALOG_MANAGER)

    def test_get_customer_permissions_admin(self, admin_client, admin_customer, regular_customer, auth_headers):
        """Test admin can view customer's permissions."""
        headers = auth_headers(admin_customer)
        
        # Customer should already have a role with permissions
        response = admin_client.get(f"/v1/admin/customers/{regular_customer.id}/permissions/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert "permissions" in data

    def test_get_customer_roles_nonexistent_customer(self, admin_client, admin_customer, auth_headers):
        """Test getting roles for non-existent customer (covers lines 150-151)."""
        headers = auth_headers(admin_customer)
        
        import uuid
        non_existent_id = str(uuid.uuid4())
        response = admin_client.get(f"/v1/admin/customers/{non_existent_id}/roles/", headers=headers)
        assert response.status_code == 404

    def test_assign_role_to_nonexistent_customer(self, admin_client, admin_customer, auth_headers):
        """Test assigning role to non-existent customer (covers lines 172-173)."""
        headers = auth_headers(admin_customer)
        
        import uuid
        non_existent_id = str(uuid.uuid4())
        response = admin_client.post(
            f"/v1/admin/customers/{non_existent_id}/roles/",
            json={"role_name": RoleName.CUSTOMER},
            headers=headers,
        )
        assert response.status_code == 404

    def test_remove_role_from_nonexistent_customer(self, admin_client, admin_customer, auth_headers):
        """Test removing role from non-existent customer (covers lines 203-204)."""
        headers = auth_headers(admin_customer)
        
        import uuid
        non_existent_id = str(uuid.uuid4())
        response = admin_client.delete(
            f"/v1/admin/customers/{non_existent_id}/roles/{RoleName.CUSTOMER}/",
            headers=headers,
        )
        assert response.status_code == 404

    def test_admin_cannot_remove_own_admin_role(self, admin_client, admin_customer, auth_headers):
        """Test admin cannot remove own admin role (covers line 208)."""
        headers = auth_headers(admin_customer)
        
        response = admin_client.delete(
            f"/v1/admin/customers/{admin_customer.id}/roles/{RoleName.ADMIN}/",
            headers=headers,
        )
        assert response.status_code in [400, 403]
        data = response.json()
        assert "нельзя" in str(data).lower() or "cannot" in str(data).lower()

    def test_remove_unassigned_role(self, admin_client, admin_customer, regular_customer, auth_headers):
        """Test removing role that wasn't assigned (covers line 217)."""
        headers = auth_headers(admin_customer)
        
        # Make sure customer doesn't have CATALOG_MANAGER role
        response = admin_client.delete(
            f"/v1/admin/customers/{regular_customer.id}/roles/{RoleName.CATALOG_MANAGER}/",
            headers=headers,
        )
        assert response.status_code == 404

    def test_get_permissions_nonexistent_customer(self, admin_client, admin_customer, auth_headers):
        """Test getting permissions for non-existent customer (covers lines 235-236)."""
        headers = auth_headers(admin_customer)
        
        import uuid
        non_existent_id = str(uuid.uuid4())
        response = admin_client.get(f"/v1/admin/customers/{non_existent_id}/permissions/", headers=headers)
        assert response.status_code == 404
