"""Схемы внутреннего admin API товаров.

Публичные схемы каталога живут в `apps/products/catalog_schemas.py` и
соответствуют контракту `contracts/catalog/*` + `contracts/shared/product`.
"""

from typing import Optional

from ninja import ModelSchema
from pydantic import ConfigDict

from .models import Category, Product, ProductImage


class CategorySchema(ModelSchema):
    """Схема Category для admin API."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {
            "id": 3,
            "slug": "dreli",
            "name": "Дрели",
            "poster": None,
            "created_at": "2024-01-10T08:00:00Z",
            "updated_at": "2024-06-01T12:00:00Z",
        }},
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {
            "id": 7,
            "image": "/media/products/bosch-gbh228-main.jpg",
            "is_primary": True,
            "order": 0,
            "created_at": "2024-03-20T09:15:00Z",
            "updated_at": "2024-03-20T09:15:00Z",
        }},
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {
            "id": 42,
            "name": "Перфоратор Bosch GBH 2-28",
            "description": "Мощный перфоратор для профессионального использования",
            "parameters": "",
            "description_parameters": [],
            "technical_specifications": [],
            "price": "12500.00",
            "sku": "BOSCH-GBH228",
            "brand": "Bosch",
            "status": "published",
            "availability": True,
            "categories": [{"id": 1, "slug": "perforatory", "name": "Перфораторы", "poster": None,
                            "created_at": "2024-01-10T08:00:00Z", "updated_at": "2024-01-10T08:00:00Z"}],
            "images": [{"id": 7, "image": "/media/products/bosch-gbh228-main.jpg", "is_primary": True,
                        "order": 0, "created_at": "2024-03-20T09:15:00Z", "updated_at": "2024-03-20T09:15:00Z"}],
            "created_at": "2024-03-15T10:00:00Z",
            "updated_at": "2024-06-10T14:30:00Z",
        }},
    )

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
