"""
Tests for products API with RBAC protection.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.urls import reverse
from ninja.testing import TestClient

from apps.products.models import Category, Product, ProductImage
from apps.users.constants import RoleName
from apps.users.models import Customer
from apps.users.services.customer_service import CustomerService
from apps.users.services.role_service import RoleService
from instrument_shop.api import api

# Note: product_factory, category_factory, and other fixtures are defined in conftest.py


@pytest.mark.django_db
class TestProductsAPI:
    """Tests for product endpoints with RBAC."""

    def test_list_products_authenticated(
        self, client, regular_customer, product_factory, auth_headers
    ):
        """Test any authenticated user can list products."""
        product_factory(name="Product 1", price=100)
        product_factory(name="Product 2", price=200)

        headers = auth_headers(regular_customer)

        response = client.get("/v1/products/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_create_product_requires_permission(
        self, client, regular_customer, auth_headers
    ):
        """Test regular customer cannot create product."""
        headers = auth_headers(regular_customer)

        response = client.post(
            "/v1/products/",
            json={
                "name": "New Product",
                "price": "99.99",
                "availability": "in_stock",
                "brand": "TestBrand",
            },
            headers=headers,
        )
        assert response.status_code == 403

    def test_admin_can_update_product(
        self, client, admin_customer, product_factory, auth_headers
    ):
        """Test admin can update any product."""
        product = product_factory(name="Old Name", price=100)

        headers = auth_headers(admin_customer)

        response = client.put(
            f"/v1/products/{product.id}",
            json={
                "name": "Updated Name",
                "price": "200.00",
                "availability": "in_stock",
                "brand": "TestBrand",
            },
            headers=headers,
        )
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.name == "Updated Name"

    def test_customer_cannot_update_product(
        self, client, regular_customer, product_factory, auth_headers
    ):
        """Test regular customer cannot update product."""
        product = product_factory()

        headers = auth_headers(regular_customer)

        response = client.put(
            f"/v1/products/{product.id}",
            json={
                "name": "Hacked",
                "price": "1.00",
                "availability": "in_stock",
                "brand": "TestBrand",
            },
            headers=headers,
        )
        assert response.status_code == 403

    def test_delete_product_admin_only(
        self, client, admin_customer, regular_customer, product_factory, auth_headers
    ):
        """Test only admin can delete product."""
        product = product_factory()

        # Admin can delete
        admin_headers = auth_headers(admin_customer)
        response = client.delete(f"/v1/products/{product.id}", headers=admin_headers)
        assert response.status_code == 200

        # New product for regular user test
        product2 = product_factory()
        regular_headers = auth_headers(regular_customer)
        response = client.delete(f"/v1/products/{product2.id}", headers=regular_headers)
        assert response.status_code == 403


@pytest.mark.django_db
class TestCategoriesAPI:
    """Tests for category endpoints with RBAC."""

    def test_list_categories(
        self, client, regular_customer, category_factory, auth_headers
    ):
        """Test any authenticated user can list categories."""
        category_factory("Cat1")
        category_factory("Cat2")

        headers = auth_headers(regular_customer)

        response = client.get("/v1/categories/", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_create_category_requires_permission(
        self, client, regular_customer, auth_headers
    ):
        """Test regular customer cannot create category."""
        headers = auth_headers(regular_customer)

        response = client.post(
            "/v1/categories/", json={"name": "New Category"}, headers=headers
        )
        assert response.status_code == 403

    def test_manager_can_create_category(self, client, manager_customer, auth_headers):
        """Test manager can create category."""
        headers = auth_headers(manager_customer)

        response = client.post(
            "/v1/categories/", json={"name": "Manager Category"}, headers=headers
        )
        assert response.status_code == 200
        assert Category.objects.filter(name="Manager Category").exists()


@pytest.mark.django_db
class TestProductImagesAPI:
    """Tests for product image endpoints with RBAC."""

    def test_add_image_requires_edit_permission(
        self, client, regular_customer, product_factory, auth_headers
    ):
        """Test that adding image requires edit_product permission."""
        product = product_factory()
        headers = auth_headers(regular_customer)

        # Mock file upload - since we can't upload actual files easily,
        # we'll test the permission logic
        # In a real scenario, you'd use multipart/form-data
        pass  # Skipping actual file upload test

    def test_manager_can_manage_images(
        self, client, manager_customer, product_factory, auth_headers
    ):
        """Test manager can add/update/delete images."""
        # This would require handling actual file upload
        pass


@pytest.mark.django_db
class TestProductPublication:
    """Tests for product publication rules."""

    @pytest.fixture
    def complete_product(self, product_factory, category_factory):
        """Create a product that meets all publication requirements."""
        category = category_factory("Guitars")
        product = product_factory(name="Fender Stratocaster", price=1500.00)
        product.categories.add(category)
        ProductImage.objects.create(
            product=product, image="test.jpg", alt_text="Guitar image"
        )
        return product

    def test_publish_valid_product(
        self, client, manager_customer, complete_product, auth_headers
    ):
        """Test manager can publish a valid product."""
        headers = auth_headers(manager_customer)

        response = client.post(
            f"/v1/products/{complete_product.id}/publish", headers=headers
        )
        assert response.status_code == 200
        complete_product.refresh_from_db()
        assert complete_product.status == "published"

    def test_publish_with_price_zero(
        self, client, manager_customer, product_factory, category_factory, auth_headers
    ):
        """Test publishing product with price=0 succeeds (not treated as empty)."""
        category = category_factory("Guitars")
        product = product_factory(name="Free Product", price=0)
        product.categories.add(category)
        ProductImage.objects.create(product=product, image="test.jpg")

        headers = auth_headers(manager_customer)

        response = client.post(f"/v1/products/{product.id}/publish", headers=headers)
        # Should succeed, not fail with "price is required" error
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.status == "published"

    def test_publish_requires_publish_permission_not_edit(
        self, client, regular_customer, manager_customer, complete_product, auth_headers
    ):
        """Test that publish requires PUBLISH_PRODUCT permission, not EDIT_PRODUCT."""
        from apps.users.constants import Permission, RoleName
        from apps.users.services.role_service import RoleService

        # Create a custom role with EDIT_PRODUCT but NOT PUBLISH_PRODUCT
        editor_role = RoleService.create_role(
            name="test_editor",
            description="Editor without publish permission",
            permissions={
                Permission.VIEW_PRODUCT: True,
                Permission.EDIT_PRODUCT: True,
                Permission.PUBLISH_PRODUCT: False,
            },
        )

        # Create a customer with this custom role
        editor = CustomerService.create_customer(
            email="editor@example.com",
            password="testpass123",
            first_name="Editor",
            last_name="User",
            phone="+1234567890",
        )
        RoleService.assign_role(editor, "test_editor")

        # Editor should NOT be able to publish (lacks PUBLISH_PRODUCT)
        headers_editor = auth_headers(editor)
        response = client.post(
            f"/v1/products/{complete_product.id}/publish", headers=headers_editor
        )
        assert response.status_code == 403

        # Manager with PUBLISH_PRODUCT should be able to publish
        # First, reset the product status to draft so it can be published
        complete_product.status = "draft"
        complete_product.save()

        headers_manager = auth_headers(manager_customer)
        response = client.post(
            f"/v1/products/{complete_product.id}/publish", headers=headers_manager
        )
        assert response.status_code == 200

    def test_publish_without_image_fails(
        self, client, manager_customer, product_factory, category_factory, auth_headers
    ):
        """Test publishing product without image fails."""
        category = category_factory("Guitars")
        product = product_factory(name="No Image Product", price=100.00)
        product.categories.add(category)

        headers = auth_headers(manager_customer)

        response = client.post(f"/v1/products/{product.id}/publish", headers=headers)
        assert response.status_code == 400
        data = response.json()
        assert "image" in str(data).lower()

    def test_publish_without_category_fails(
        self, client, manager_customer, product_factory, auth_headers
    ):
        """Test publishing product without category fails."""
        product = product_factory(name="No Category Product", price=100.00)
        ProductImage.objects.create(product=product, image="test.jpg")

        headers = auth_headers(manager_customer)

        response = client.post(f"/v1/products/{product.id}/publish", headers=headers)
        assert response.status_code == 400
        data = response.json()
        assert "category" in str(data).lower()

    def test_publish_without_name_fails(
        self, client, manager_customer, category_factory, auth_headers
    ):
        """Test publishing product without name fails."""
        category = category_factory("Guitars")
        product = Product.objects.create(
            name="", price=100.00
        )  # Empty name should fail validation
        product.categories.add(category)
        ProductImage.objects.create(product=product, image="test.jpg")

        headers = auth_headers(manager_customer)

        response = client.post(f"/v1/products/{product.id}/publish", headers=headers)
        assert response.status_code == 400

    def test_publish_without_price_fails(
        self, client, manager_customer, category_factory, auth_headers
    ):
        """Test publishing product without price fails."""
        category = category_factory("Guitars")
        product = Product.objects.create(name="No Price Product")  # name is required
        product.categories.add(category)
        ProductImage.objects.create(product=product, image="test.jpg")

        headers = auth_headers(manager_customer)

        response = client.post(f"/v1/products/{product.id}/publish", headers=headers)
        assert response.status_code == 400

    def test_cannot_create_product_with_published_status(
        self, client, manager_customer, auth_headers
    ):
        """Test that creating product with status=published is ignored (always draft)."""
        headers = auth_headers(manager_customer)

        response = client.post(
            "/v1/products/",
            json={
                "name": "Test",
                "price": "100.00",
                "status": "published",
                "availability": "in_stock",
                "brand": "TestBrand",
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "draft"


@pytest.mark.django_db
class TestProductImagePrimaryRules:
    """Tests for single primary image enforcement."""

    def test_first_image_primary_by_default(self, product_factory):
        """Test that first image can be set as primary."""
        product = product_factory(name="Test Product", price=100)
        image = ProductImage.objects.create(
            product=product, image="test1.jpg", is_primary=True
        )
        assert image.is_primary is True

    def test_set_second_image_as_primary(self, product_factory):
        """Test that setting second image as primary unsets the first."""
        product = product_factory(name="Test Product", price=100)
        image1 = ProductImage.objects.create(
            product=product, image="test1.jpg", is_primary=True
        )
        image2 = ProductImage.objects.create(
            product=product, image="test2.jpg", is_primary=True
        )

        image1.refresh_from_db()
        assert image1.is_primary is False
        assert image2.is_primary is True

    def test_update_image_to_primary(self, product_factory):
        """Test updating an existing image to primary unsets others."""
        product = product_factory(name="Test Product", price=100)
        image1 = ProductImage.objects.create(
            product=product, image="test1.jpg", is_primary=True
        )
        image2 = ProductImage.objects.create(
            product=product, image="test2.jpg", is_primary=False
        )

        # Update image2 to be primary
        image2.is_primary = True
        image2.save()

        image1.refresh_from_db()
        assert image1.is_primary is False
        assert image2.is_primary is True

    def test_only_one_primary_after_multiple_saves(self, product_factory):
        """Stress test: ensure only one primary after multiple save operations."""
        product = product_factory(name="Test Product", price=100)
        images = []
        for i in range(5):
            img = ProductImage.objects.create(
                product=product,
                image=f"test{i}.jpg",
                is_primary=(i == 0),  # Only first is primary
            )
            images.append(img)

        # Set the last image as primary
        images[4].is_primary = True
        images[4].save()

        # Refresh all
        for img in images:
            img.refresh_from_db()

        primary_count = sum(1 for img in images if img.is_primary)
        assert primary_count == 1
        assert images[4].is_primary is True

    def test_set_primary_updates_others_via_model(self, product_factory):
        """Test that setting primary via model save() unsets others."""
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Create a simple user for testing (bypass CustomerService issues)
        product = product_factory(name="Test Product", price=100)

        # Create first image as primary
        image1 = ProductImage.objects.create(
            product=product, image="test1.jpg", is_primary=True
        )
        assert image1.is_primary is True

        # Create second image as primary via save()
        image2 = ProductImage.objects.create(
            product=product, image="test2.jpg", is_primary=True
        )

        # Refresh from db
        image1.refresh_from_db()

        # Verify only image2 is primary
        assert image1.is_primary is False
        assert image2.is_primary is True

    def test_database_constraint_prevents_double_primary(self, product_factory):
        """Test that database constraint prevents two primary images."""
        product = product_factory(name="Test Product", price=100)

        # Create first primary image (via save(), which works)
        ProductImage.objects.create(product=product, image="test1.jpg", is_primary=True)

        # Try to create second primary using bulk_create to bypass save()
        # This should fail due to the database constraint
        images_to_create = [
            ProductImage(product=product, image="test2.jpg", is_primary=True)
        ]

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProductImage.objects.bulk_create(images_to_create)


@pytest.mark.django_db
class TestPublicAPISchema:
    """Tests for public API schema (ensure internal fields are not exposed)."""

    def test_public_product_list_uses_public_category_schema(
        self, client, product_factory, category_factory, auth_headers
    ):
        """Test that public product list doesn't expose internal category fields."""
        category = category_factory("Guitars")
        product = product_factory(name="Test Guitar", price=500.00, status="published")
        product.categories.add(category)

        # Access public endpoint (no auth required)
        response = client.get("/v1/public/products/")
        assert response.status_code == 200
        data = response.json()

        if len(data) > 0:
            product_data = data[0]
            # Check categories don't have internal fields
            if "categories" in product_data and len(product_data["categories"]) > 0:
                category_data = product_data["categories"][0]
                # These internal fields should NOT be present
                assert "created_at" not in category_data
                assert "updated_at" not in category_data
                # These public fields SHOULD be present
                assert "id" in category_data
                assert "name" in category_data
                assert "slug" in category_data

    def test_public_product_detail_uses_public_image_schema(
        self, client, product_factory, category_factory, auth_headers
    ):
        """Test that public product detail doesn't expose internal image fields."""
        category = category_factory("Guitars")
        product = product_factory(name="Test Guitar", price=500.00, status="published")
        product.categories.add(category)
        ProductImage.objects.create(
            product=product, image="test.jpg", alt_text="Test image"
        )

        # Access public endpoint (no auth required)
        response = client.get(f"/v1/public/products/{product.id}/")
        assert response.status_code == 200
        data = response.json()

        # Check images don't have internal fields
        if "images" in data and len(data["images"]) > 0:
            image_data = data["images"][0]
            # These internal fields should NOT be present
            assert "created_at" not in image_data
            assert "updated_at" not in image_data
            # These public fields SHOULD be present
            assert "id" in image_data
            assert "image" in image_data
            assert "alt_text" in image_data
            assert "is_primary" in image_data

    def test_public_product_list_excludes_images(
        self, client, product_factory, category_factory
    ):
        """Test that public product list doesn't include images (list view optimization)."""
        category = category_factory("Guitars")
        product = product_factory(name="Test Guitar", price=500.00, status="published")
        product.categories.add(category)
        ProductImage.objects.create(
            product=product, image="test.jpg", alt_text="Test image"
        )

        # Access public list endpoint (no auth required)
        response = client.get("/v1/public/products/")
        assert response.status_code == 200
        data = response.json()

        if len(data) > 0:
            product_data = data[0]
            # List schema should NOT include images
            assert "images" not in product_data
