"""
Public API endpoints for storefront (no authentication required).
"""

from typing import Optional

from django.core.cache import cache
from django.db.models import QuerySet
from django.http import HttpRequest
from django_ratelimit.decorators import ratelimit
from ninja import Query, Router

from .models import Category, Product, ProductStatusChoices
from .schemas import PublicCategorySchema, PublicProductListSchema, PublicProductSchema

# ============================================================================
# Public Router
# ============================================================================
public_router = Router(tags=["Public Storefront"])


@public_router.get("/categories/", response=list[PublicCategorySchema])
@ratelimit(key="ip", rate="100/m", method="GET", block=True)
def list_public_categories(request: HttpRequest):
    """
    List all categories for public storefront.
    No authentication required.
    Returns: id, name, slug
    """
    cache_key = "public:categories:list"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    categories = list(Category.objects.all())
    cache.set(cache_key, categories, 300)  # 5 minutes
    return categories


def apply_product_filters(
    queryset: QuerySet,
    category_id: Optional[int] = None,
    category_slug: Optional[str] = None,
    search: Optional[str] = None,
) -> QuerySet:
    """Apply filters to product queryset."""
    # Filter by category_id
    if category_id is not None:
        queryset = queryset.filter(categories__id=category_id)

    # Filter by category_slug
    if category_slug is not None:
        queryset = queryset.filter(categories__slug=category_slug)

    # Search by name
    if search:
        queryset = queryset.filter(name__icontains=search)

    return queryset.distinct()


@public_router.get("/products/", response=list[PublicProductListSchema])
@ratelimit(key="ip", rate="100/m", method="GET", block=True)
def list_public_products(
    request: HttpRequest,
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    category_slug: Optional[str] = Query(None, description="Filter by category slug"),
    search: Optional[str] = Query(None, description="Search by product name"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Max items to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of items to skip"),
):
    """
    List published products for public storefront.
    No authentication required.
    Filters:
        - category_id: filter by category ID
        - category_slug: filter by category slug
        - search: search by product name (icontains)
    Pagination:
        - limit: max items to return (1-100, default 20)
        - offset: number of items to skip (default 0)
    """
    # Create stable cache key based on query params (sorted for consistency)
    params = sorted(request.GET.items())
    cache_key = (
        f"public:products:list:{params}" if params else "public:products:list:all"
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    queryset = (
        Product.objects.select_related()
        .prefetch_related("categories", "images")
        .filter(status=ProductStatusChoices.PUBLISHED)
    )

    queryset = apply_product_filters(
        queryset,
        category_id=category_id,
        category_slug=category_slug,
        search=search,
    )

    products = list(queryset[offset : offset + limit])
    cache.set(cache_key, products, 60)  # 1 minute
    return products


@public_router.get("/products/{int:product_id}/", response=PublicProductSchema)
@ratelimit(key="ip", rate="100/m", method="GET", block=True)
def get_public_product(request: HttpRequest, product_id: int):
    """
    Get a single published product for public storefront.
    No authentication required.
    Only returns published products.
    """
    from django.shortcuts import get_object_or_404

    cache_key = f"public:products:detail:{product_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    product = (
        Product.objects.select_related()
        .prefetch_related("categories", "images")
        .filter(status=ProductStatusChoices.PUBLISHED)
    )

    result = get_object_or_404(product, pk=product_id)
    cache.set(cache_key, result, 300)  # 5 minutes
    return result
