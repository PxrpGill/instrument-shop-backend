from django.shortcuts import get_object_or_404
from ninja import Router
from typing import List

from .models import Category, Product
from .schemas import (
    CategorySchema,
    CategoryCreateSchema,
    ProductSchema,
    ProductCreateSchema,
    ProductUpdateSchema,
)

router = Router()


@router.get("/categories", response=List[CategorySchema])
def list_categories(request):
    """List all categories."""
    return Category.objects.all()


@router.get("/categories/{int:category_id}", response=CategorySchema)
def get_category(request, category_id: int):
    """Get a single category by ID."""
    return get_object_or_404(Category, pk=category_id)


@router.post("/categories", response=CategorySchema)
def create_category(request, payload: CategoryCreateSchema):
    """Create a new category."""
    category = Category.objects.create(**payload.dict())
    return category


@router.put("/categories/{int:category_id}", response=CategorySchema)
def update_category(request, category_id: int, payload: CategoryCreateSchema):
    """Update an existing category."""
    category = get_object_or_404(Category, pk=category_id)
    for key, value in payload.dict().items():
        setattr(category, key, value)
    category.save()
    return category


@router.delete("/categories/{int:category_id}")
def delete_category(request, category_id: int):
    """Delete a category."""
    category = get_object_or_404(Category, pk=category_id)
    category.delete()
    return {"success": True}


# Product endpoints
@router.get("/products", response=List[ProductSchema])
def list_products(request):
    """List all products."""
    return Product.objects.select_related().prefetch_related("categories").all()


@router.get("/products/{int:product_id}", response=ProductSchema)
def get_product(request, product_id: int):
    """Get a single product by ID."""
    return get_object_or_404(
        Product.objects.select_related().prefetch_related("categories"), pk=product_id
    )


@router.post("/products", response=ProductSchema)
def create_product(request, payload: ProductCreateSchema):
    """Create a new product."""
    data = payload.dict()
    category_ids = data.pop("category_ids", [])
    product = Product.objects.create(**data)
    if category_ids:
        categories = Category.objects.filter(pk__in=category_ids)
        product.categories.set(categories)
    return product


@router.put("/products/{int:product_id}", response=ProductSchema)
def update_product(request, product_id: int, payload: ProductUpdateSchema):
    """Update an existing product."""
    product = get_object_or_404(Product, pk=product_id)
    for key, value in payload.dict().items():
        setattr(product, key, value)
    product.save()
    return product


@router.delete("/products/{int:product_id}")
def delete_product(request, product_id: int):
    """Delete a product."""
    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    return {"success": True}


@router.get("/categories/{int:category_id}/products", response=List[ProductSchema])
def list_products_by_category(request, category_id: int):
    """List products by category."""
    category = get_object_or_404(Category, pk=category_id)
    return (
        Product.objects.select_related()
        .prefetch_related("categories")
        .filter(categories=category)
    )
