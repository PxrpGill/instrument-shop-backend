from typing import Optional

from ninja import ModelSchema

from .models import (Category, Product, ProductAvailabilityChoices,
                     ProductImage, ProductStatusChoices)


class CategorySchema(ModelSchema):
    """Schema for Category output."""

    class Meta:
        model = Category
        fields = ["id", "slug", "name", "image", "created_at", "updated_at"]


class CategoryCreateSchema(ModelSchema):
    """Schema for Category creation."""

    class Meta:
        model = Category
        fields = ["name", "image"]


class PublicCategorySchema(ModelSchema):
    """Public schema for Category (storefront only)."""

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductImageSchema(ModelSchema):
    """Schema for ProductImage output."""

    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_primary", "created_at", "updated_at"]


class ProductImageCreateSchema(ModelSchema):
    """Schema for ProductImage creation."""

    class Meta:
        model = ProductImage
        fields = ["image", "alt_text", "is_primary"]


class ProductSchema(ModelSchema):
    """Schema for Product output."""

    categories: Optional[list[CategorySchema]] = []
    images: Optional[list[ProductImageSchema]] = []

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "parameters",
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
    """Schema for Product creation. Status is always set to draft."""

    category_ids: Optional[list[int]] = []

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "parameters",
            "price",
            "sku",
            "brand",
            "availability",
        ]


class ProductUpdateSchema(ModelSchema):
    """Schema for Product update. Status cannot be changed directly."""

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "parameters",
            "price",
            "sku",
            "brand",
            "availability",
        ]


class PublicProductSchema(ModelSchema):
    """Public schema for Product (storefront only)."""

    categories: Optional[list[CategorySchema]] = []
    images: Optional[list[ProductImageSchema]] = []

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "brand",
            "availability",
            "categories",
            "created_at",
        ]


class PublicProductListSchema(ModelSchema):
    """Public schema for Product list (minimal data, no images for list view)."""

    categories: Optional[list[CategorySchema]] = []

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "price",
            "brand",
            "availability",
            "categories",
        ]
