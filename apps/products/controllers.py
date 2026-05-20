from typing import List

from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja import Router

from apps.users.api.auth_helpers import get_customer_from_request
from apps.users.constants import Permission
from core.auth.permissions import HasPermission, HasRoleMixin, IsAuthenticated

from .models import Category, Product, ProductImage, ProductStatusChoices
from .schemas import (CategoryCreateSchema, CategorySchema,
                      ProductCreateSchema, ProductImageCreateSchema,
                      ProductImageSchema, ProductSchema, ProductUpdateSchema)
from .services import ProductPublicationError, ProductPublicationService

# =============================================================================
# Cache Invalidation Helpers
# =============================================================================


def invalidate_public_cache() -> None:
    """Invalidate all public cache keys."""
    try:
        from django_redis import get_redis_connection

        redis_client = get_redis_connection("default")
        for key in redis_client.keys("instrument_shop:public:products:*"):
            redis_client.delete(key)
    except Exception:
        # Fallback to known keys only on error
        pass

    # Always delete these keys explicitly
    cache.delete("public:categories:list")


def invalidate_product_detail_cache(product_id: int) -> None:
    """Invalidate cache for a specific product."""
    cache.delete(f"public:products:detail:{product_id}")


# ============================================================================
# Categories Router
# ============================================================================
categories_router = Router(tags=["Categories"])


# Anyone with view_category permission can list/view categories
@categories_router.get("", response=List[CategorySchema])
def list_categories(request):
    """List all categories. Requires view_category permission."""
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.VIEW_CATEGORY)
    return Category.objects.all()


@categories_router.post("", response=CategorySchema)
def create_category(request, payload: CategoryCreateSchema):
    """
    Create a new category.
    Requires create_category permission (admin/manager).
    """
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.CREATE_CATEGORY)
    category = Category.objects.create(**payload.dict())
    invalidate_public_cache()
    return category


@categories_router.get("/{int:category_id}", response=CategorySchema)
def get_category(request, category_id: int):
    """Get a single category by ID. Requires view_category permission."""
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.VIEW_CATEGORY)
    return get_object_or_404(Category, pk=category_id)


@categories_router.put("/{int:category_id}", response=CategorySchema)
def update_category(request, category_id: int, payload: CategoryCreateSchema):
    """
    Update an existing category.
    Requires edit_category permission (admin/manager).
    """
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.EDIT_CATEGORY)
    category = get_object_or_404(Category, pk=category_id)
    for key, value in payload.dict().items():
        setattr(category, key, value)
    category.save()
    invalidate_public_cache()
    return category


@categories_router.delete("/{int:category_id}")
def delete_category(request, category_id: int):
    """
    Delete a category.
    Requires delete_category permission (admin only typically).
    """
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.DELETE_CATEGORY)
    category = get_object_or_404(Category, pk=category_id)
    category.delete()
    invalidate_public_cache()
    return {"success": True}


@categories_router.get("/{int:category_id}/products", response=List[ProductSchema])
def list_products_by_category(request, category_id: int):
    """List products by category. Requires view_product permission."""
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.VIEW_PRODUCT)
    category = get_object_or_404(Category, pk=category_id)
    return (
        Product.objects.select_related()
        .prefetch_related("categories")
        .filter(categories=category)
    )


# ============================================================================
# Products Router
# ============================================================================
router = Router(tags=["Products"])


@router.get("", response=List[ProductSchema])
def list_products(request):
    """List all products. Requires view_product permission."""
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.VIEW_PRODUCT)
    return Product.objects.select_related().prefetch_related("categories").all()


@router.post("", response=ProductSchema)
def create_product(request, payload: ProductCreateSchema):
    """
    Create a new product.
    Requires create_product permission (admin/manager).
    """
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.CREATE_PRODUCT)
    data = payload.dict()
    category_ids = data.pop("category_ids", [])
    product = Product.objects.create(**data)
    if category_ids:
        categories = Category.objects.filter(pk__in=category_ids)
        product.categories.set(categories)
    invalidate_public_cache()
    return product


@router.get("/{int:product_id}", response=ProductSchema)
def get_product(request, product_id: int):
    """Get a single product by ID. Requires view_product permission."""
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.VIEW_PRODUCT)
    return get_object_or_404(
        Product.objects.select_related().prefetch_related("categories"), pk=product_id
    )


@router.put("/{int:product_id}", response=ProductSchema)
def update_product(request, product_id: int, payload: ProductUpdateSchema):
    """
    Update an existing product.
    Requires edit_product permission (admin/manager).
    """
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.EDIT_PRODUCT)
    product = get_object_or_404(Product, pk=product_id)
    for key, value in payload.dict().items():
        setattr(product, key, value)
    product.save()
    invalidate_product_detail_cache(product_id)
    invalidate_public_cache()
    return product


@router.post("/{int:product_id}/publish", response=ProductSchema)
def publish_product(request, product_id: int):
    """
    Publish a product.
    Requires publish_product permission (admin/catalog_manager).
    Validates publication readiness (name, price, image, category).
    """
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.PUBLISH_PRODUCT)
    product = get_object_or_404(Product, pk=product_id)
    errors = ProductPublicationService.get_publication_errors(product)
    if errors:
        raise ProductPublicationError(errors)
    product.status = ProductStatusChoices.PUBLISHED
    product.save()
    invalidate_product_detail_cache(product_id)
    invalidate_public_cache()
    return product


@router.delete("/{int:product_id}")
def delete_product(request, product_id: int):
    """
    Delete a product.
    Requires delete_product permission (admin only).
    """
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.DELETE_PRODUCT)
    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    invalidate_product_detail_cache(product_id)
    invalidate_public_cache()
    return {"success": True}


# ============================================================================
# Product Images Router (sub-router for nested resource)
# ============================================================================
images_router = Router(tags=["Product Images"])


@images_router.get("/{int:product_id}/images", response=List[ProductImageSchema])
def list_product_images(request, product_id: int):
    """List all images for a product. Requires view_product permission."""
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.VIEW_PRODUCT)
    product = get_object_or_404(Product, pk=product_id)
    return product.images.all()


@images_router.post("/{int:product_id}/images", response=ProductImageSchema)
def create_product_image(request, product_id: int, payload: ProductImageCreateSchema):
    """
    Add an image to a product.
    Requires edit_product permission (admin/manager).
    """
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.EDIT_PRODUCT)
    product = get_object_or_404(Product, pk=product_id)
    image = ProductImage.objects.create(product=product, **payload.dict())
    invalidate_product_detail_cache(product_id)
    return image


@images_router.put(
    "/{int:product_id}/images/{int:image_id}", response=ProductImageSchema
)
def update_product_image(
    request, product_id: int, image_id: int, payload: ProductImageCreateSchema
):
    """
    Update a product image.
    Requires edit_product permission (admin/manager).
    """
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.EDIT_PRODUCT)
    product = get_object_or_404(Product, pk=product_id)
    image = get_object_or_404(ProductImage, pk=image_id, product=product)
    for key, value in payload.dict().items():
        setattr(image, key, value)
    image.save()
    invalidate_product_detail_cache(product_id)
    return image


@images_router.delete("/{int:product_id}/images/{int:image_id}")
def delete_product_image(request, product_id: int, image_id: int):
    """
    Delete a product image.
    Requires edit_product permission (admin/manager).
    """
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.EDIT_PRODUCT)
    product = get_object_or_404(Product, pk=product_id)
    image = get_object_or_404(ProductImage, pk=image_id, product=product)
    image.delete()
    invalidate_product_detail_cache(product_id)
    return {"success": True}
