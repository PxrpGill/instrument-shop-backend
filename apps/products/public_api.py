"""
Public API endpoints for storefront (no authentication required).
"""

from typing import Optional

from django.db.models import QuerySet
from ninja import Query, Router

from .models import Category, Product, ProductStatusChoices
from .schemas import (PublicCategorySchema, PublicProductListSchema,
                      PublicProductSchema)

# ============================================================================
# Public Router
# ============================================================================
public_router = Router()


@public_router.get("/categories/", response=list[PublicCategorySchema])
def list_public_categories(request):
    """
    List all categories for public storefront.
    No authentication required.
    Returns: id, name, slug
    """
    return Category.objects.all()


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
def list_public_products(
    request,
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

    return queryset[offset : offset + limit]


@public_router.get("/products/{int:product_id}/", response=PublicProductSchema)
def get_public_product(request, product_id: int):
    """
    Get a single published product for public storefront.
    No authentication required.
    Only returns published products.
    """
    from django.shortcuts import get_object_or_404

    product = (
        Product.objects.select_related()
        .prefetch_related("categories", "images")
        .filter(status=ProductStatusChoices.PUBLISHED)
    )

    return get_object_or_404(product, pk=product_id)
