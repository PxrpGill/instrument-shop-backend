"""
Tests for public API (storefront endpoints without authentication).
"""

import pytest
from django.test import Client

from apps.products.models import Category, Product, ProductImage, ProductStatusChoices


@pytest.fixture
def public_client():
    """Django test client for public endpoints."""
    return Client()


@pytest.fixture
def category_factory():
    """Factory to create test categories."""

    def create_category(name="Test Category", slug=None):
        if slug is None:
            slug = name.lower().replace(" ", "-")
        return Category.objects.create(name=name, slug=slug)

    return create_category


@pytest.fixture
def product_factory():
    """Factory to create test products."""

    def create_product(
        name="Test Product",
        price=100.00,
        status=ProductStatusChoices.DRAFT,
        categories=None,
    ):
        product = Product.objects.create(
            name=name,
            price=price,
            status=status,
        )
        if categories:
            product.categories.set(categories)
        return product

    return create_product


@pytest.fixture
def product_image_factory():
    """Factory to create test product images."""

    def create_image(product, image="test.jpg", is_primary=False):
        return ProductImage.objects.create(
            product=product,
            image=image,
            is_primary=is_primary,
        )

    return create_image


@pytest.mark.django_db
class TestPublicCategories:
    """Tests for public categories endpoint."""

    def test_list_categories_no_auth_required(self, public_client, category_factory):
        """Test guest can list categories without authentication."""
        category_factory("Guitars")
        category_factory("Drums")

        response = public_client.get("/api/v1/public/categories/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_categories_return_correct_fields(self, public_client, category_factory):
        """Test categories return only public fields (id, name, slug)."""
        category = category_factory("Guitars", "guitars")

        response = public_client.get("/api/v1/public/categories/")
        assert response.status_code == 200
        data = response.json()[0]
        assert "id" in data
        assert "name" in data
        assert "slug" in data
        # Should not include internal fields
        assert "image" not in data
        assert "created_at" not in data


@pytest.mark.django_db
class TestPublicProducts:
    """Tests for public products endpoints."""

    def test_list_products_no_auth_required(self, public_client, product_factory):
        """Test guest can list products without authentication."""
        product_factory(
            name="Product 1", price=100, status=ProductStatusChoices.PUBLISHED
        )
        product_factory(
            name="Product 2", price=200, status=ProductStatusChoices.PUBLISHED
        )

        response = public_client.get("/api/v1/public/products/")
        assert response.status_code == 200

    def test_list_products_returns_only_published(
        self, public_client, product_factory, category_factory
    ):
        """Test guest only sees published products, not drafts."""
        category = category_factory("Guitars")
        product_factory(
            name="Published Product",
            price=100,
            status=ProductStatusChoices.PUBLISHED,
            categories=[category],
        )
        product_factory(
            name="Draft Product",
            price=200,
            status=ProductStatusChoices.DRAFT,
            categories=[category],
        )
        product_factory(
            name="Archived Product",
            price=300,
            status=ProductStatusChoices.ARCHIVED,
            categories=[category],
        )

        response = public_client.get("/api/v1/public/products/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Published Product"

    def test_list_products_filter_by_category_id(
        self, public_client, product_factory, category_factory
    ):
        """Test filter products by category_id."""
        guitars = category_factory("Guitars")
        drums = category_factory("Drums")

        product_factory(
            name="Guitar 1",
            price=100,
            categories=[guitars],
            status=ProductStatusChoices.PUBLISHED,
        )
        product_factory(
            name="Guitar 2",
            price=200,
            categories=[guitars],
            status=ProductStatusChoices.PUBLISHED,
        )
        product_factory(
            name="Drum 1",
            price=300,
            categories=[drums],
            status=ProductStatusChoices.PUBLISHED,
        )

        response = public_client.get(
            f"/api/v1/public/products/?category_id={guitars.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_products_filter_by_category_slug(
        self, public_client, product_factory, category_factory
    ):
        """Test filter products by category_slug."""
        guitars = category_factory("Guitars", "guitars")
        drums = category_factory("Drums", "drums")

        product_factory(
            name="Guitar 1",
            price=100,
            categories=[guitars],
            status=ProductStatusChoices.PUBLISHED,
        )
        product_factory(
            name="Drum 1",
            price=300,
            categories=[drums],
            status=ProductStatusChoices.PUBLISHED,
        )

        response = public_client.get("/api/v1/public/products/?category_slug=guitars")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Guitar 1"

    def test_list_products_search_by_name(
        self, public_client, product_factory, category_factory
    ):
        """Test search products by name."""
        category = category_factory("Guitars")

        product_factory(
            name="Fender Stratocaster",
            price=1500,
            categories=[category],
            status=ProductStatusChoices.PUBLISHED,
        )
        product_factory(
            name="Gibson Les Paul",
            price=2500,
            categories=[category],
            status=ProductStatusChoices.PUBLISHED,
        )
        product_factory(
            name="Yamaha Acoustic",
            price=500,
            categories=[category],
            status=ProductStatusChoices.PUBLISHED,
        )

        response = public_client.get("/api/v1/public/products/?search=Fender")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Fender Stratocaster"

    def test_list_products_search_case_insensitive(
        self, public_client, product_factory, category_factory
    ):
        """Test search is case insensitive."""
        category = category_factory("Guitars")

        product_factory(
            name="FENDER Stratocaster",
            price=1500,
            categories=[category],
            status=ProductStatusChoices.PUBLISHED,
        )

        response = public_client.get("/api/v1/public/products/?search=fender")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_products_pagination(
        self, public_client, product_factory, category_factory
    ):
        """Test pagination with limit and offset."""
        category = category_factory("Guitars")

        for i in range(5):
            product_factory(
                name=f"Product {i+1}",
                price=100 * (i + 1),
                categories=[category],
                status=ProductStatusChoices.PUBLISHED,
            )

        # Default limit should be 20
        response = public_client.get("/api/v1/public/products/")
        assert response.status_code == 200
        assert len(response.json()) == 5

        # Custom limit
        response = public_client.get("/api/v1/public/products/?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Offset
        response = public_client.get("/api/v1/public/products/?limit=2&offset=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_product_detail_published_only(
        self, public_client, product_factory, category_factory, product_image_factory
    ):
        """Test can get published product detail."""
        category = category_factory("Guitars")
        product = product_factory(
            name="Fender Stratocaster",
            price=1500,
            status=ProductStatusChoices.PUBLISHED,
            categories=[category],
        )
        product_image_factory(product, is_primary=True)

        response = public_client.get(f"/api/v1/public/products/{product.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Fender Stratocaster"

    def test_get_product_detail_draft_not_found(self, public_client, product_factory):
        """Test cannot get draft product detail."""
        product = product_factory(
            name="Draft Product", price=100, status=ProductStatusChoices.DRAFT
        )

        response = public_client.get(f"/api/v1/public/products/{product.id}/")
        assert response.status_code == 404

    def test_get_product_detail_archived_not_found(
        self, public_client, product_factory
    ):
        """Test cannot get archived product detail."""
        product = product_factory(
            name="Archived Product", price=100, status=ProductStatusChoices.ARCHIVED
        )

        response = public_client.get(f"/api/v1/public/products/{product.id}/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestPublicProductFilters:
    """Tests for combined public product filters."""

    def test_category_and_search_together(
        self, public_client, product_factory, category_factory
    ):
        """Test filtering by category and searching together."""
        guitars = category_factory("Guitars")

        product_factory(
            name="Fender Stratocaster",
            price=1500,
            categories=[guitars],
            status=ProductStatusChoices.PUBLISHED,
        )
        product_factory(
            name="Fender Telecaster",
            price=1200,
            categories=[guitars],
            status=ProductStatusChoices.PUBLISHED,
        )
        product_factory(
            name="Gibson Les Paul",
            price=2500,
            categories=[guitars],
            status=ProductStatusChoices.PUBLISHED,
        )

        response = public_client.get(
            f"/api/v1/public/products/?category_id={guitars.id}&search=Fender"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("Fender" in p["name"] for p in data)
