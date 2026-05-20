"""Схемы внутреннего admin API товаров.

Публичные схемы каталога живут в `apps/products/catalog_schemas.py` и
соответствуют контракту `contracts/catalog/*` + `contracts/shared/product`.
"""

from typing import Optional

from ninja import ModelSchema

from .models import Category, Product, ProductImage


class CategorySchema(ModelSchema):
    """Схема Category для admin API."""

    class Meta:
        model = Category
        fields = ["id", "slug", "name", "poster", "created_at", "updated_at"]


class CategoryCreateSchema(ModelSchema):
    """Схема создания/обновления Category."""

    class Meta:
        model = Category
        fields = ["name", "poster"]


class ProductImageSchema(ModelSchema):
    """Схема ProductImage для admin API."""

    class Meta:
        model = ProductImage
        fields = [
            "id",
            "image",
            "is_primary",
            "order",
            "created_at",
            "updated_at",
        ]


class ProductImageCreateSchema(ModelSchema):
    """Схема привязки изображения к товару."""

    class Meta:
        model = ProductImage
        fields = ["image", "is_primary", "order"]


class ProductSchema(ModelSchema):
    """Схема Product для admin API."""

    categories: Optional[list[CategorySchema]] = []
    images: Optional[list[ProductImageSchema]] = []

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "parameters",
            "description_parameters",
            "technical_specifications",
            "price",
            "sku",
            "brand",
            "status",
            "availability",
            "categories",
            "created_at",
            "updated_at",
        ]


class ProductCreateSchema(ModelSchema):
    """Схема создания товара. status всегда выставляется в draft на бэке."""

    category_ids: Optional[list[int]] = []

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "parameters",
            "description_parameters",
            "technical_specifications",
            "price",
            "sku",
            "brand",
            "availability",
        ]


class ProductUpdateSchema(ModelSchema):
    """Схема обновления товара. status меняется только через /publish."""

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "parameters",
            "description_parameters",
            "technical_specifications",
            "price",
            "sku",
            "brand",
            "availability",
        ]
