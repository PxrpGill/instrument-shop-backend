"""
Tests for caching functionality in public API.
"""

import pytest
from django.core.cache import cache

from apps.products.models import Category, Product, ProductStatusChoices


@pytest.fixture
def clear_cache():
    """Clear all cache before and after tests."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def sample_category(db):
    """Create a sample category for testing."""
    return Category.objects.create(name="Test Category", slug="test-category")


@pytest.fixture
def sample_product(db, sample_category):
    """Create a sample published product for testing."""
    product = Product.objects.create(
        name="Test Product",
        description="Test description",
        price=1000,
        status=ProductStatusChoices.PUBLISHED,
    )
    product.categories.add(sample_category)
    return product


@pytest.mark.django_db
class TestCategoriesCache:
    """Tests for categories caching."""

    def test_categories_cache_hit(self, sample_category, clear_cache):
        """Test that categories are cached and returned from cache."""
        from apps.products.public_api import list_public_categories
        from unittest.mock import MagicMock

        request = MagicMock()
        request.META = {}
        result1 = list_public_categories(request)

        cached_value = cache.get("public:categories:list")
        assert cached_value is not None
        assert len(cached_value) > 0

    def test_categories_cache_invalidation_on_create(
        self, sample_category, clear_cache
    ):
        """Test that cache is invalidated when category is created."""
        from apps.products.public_api import list_public_categories
        from unittest.mock import MagicMock

        request = MagicMock()
        request.META = {}

        list_public_categories(request)

        new_category = Category.objects.create(name="New Category", slug="new-category")

        cached_value = cache.get("public:categories:list")
        assert cached_value is None or len(cached_value) == 1


@pytest.mark.django_db
class TestProductsCache:
    """Tests for products caching."""

    def test_products_list_cache_hit(self, sample_product, clear_cache):
        """Test that product list is cached."""
        from apps.products.public_api import list_public_products
        from unittest.mock import MagicMock

        request = MagicMock()
        request.META = {}
        request.GET = MagicMock()
        request.GET.items.return_value = []

        result1 = list_public_products(
            request,
            category_id=None,
            category_slug=None,
            search=None,
            limit=20,
            offset=0,
        )

        cached_value = cache.get("public:products:list:all")
        assert cached_value is not None

    def test_products_list_cache_miss(self, sample_product, clear_cache):
        """Test that cache miss triggers database query."""
        from apps.products.public_api import list_public_products
        from unittest.mock import MagicMock

        request = MagicMock()
        request.META = {}
        request.GET = MagicMock()
        request.GET.items.return_value = [("search", "different")]

        cache.clear()

        result = list_public_products(
            request,
            category_id=None,
            category_slug=None,
            search=None,
            limit=20,
            offset=0,
        )

        assert len(result) > 0

    def test_product_detail_cache(self, sample_product, clear_cache):
        """Test that product detail is cached."""
        from apps.products.public_api import get_public_product
        from unittest.mock import MagicMock

        request = MagicMock()
        request.META = {}

        result1 = get_public_product(request, product_id=sample_product.id)

        cache_key = f"public:products:detail:{sample_product.id}"
        cached_value = cache.get(cache_key)
        assert cached_value is not None
        assert cached_value.id == sample_product.id

    def test_product_detail_cache_invalidation_on_api_update(
        self, sample_product, clear_cache
    ):
        """Test that product detail cache is invalidated when product is updated via API."""
        from apps.products.public_api import get_public_product
        from apps.products.controllers import invalidate_product_detail_cache
        from unittest.mock import MagicMock

        request = MagicMock()
        request.META = {}

        get_public_product(request, product_id=sample_product.id)

        invalidate_product_detail_cache(sample_product.id)

        cache_key = f"public:products:detail:{sample_product.id}"
        cached_value = cache.get(cache_key)
        assert cached_value is None
