from ninja import ModelSchema
from .models import Category, Product, ProductImage


class CategorySchema(ModelSchema):
    """Schema for Category output."""
    class Meta:
        model = Category
        fields = ['id', 'slug', 'name', 'image', 'created_at', 'updated_at']


class CategoryCreateSchema(ModelSchema):
    """Schema for Category creation."""
    class Meta:
        model = Category
        fields = ['name', 'image']


class ProductImageSchema(ModelSchema):
    """Schema for ProductImage output."""
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'created_at', 'updated_at']


class ProductImageCreateSchema(ModelSchema):
    """Schema for ProductImage creation."""
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary']


class ProductSchema(ModelSchema):
    """Schema for Product output."""
    categories: list[CategorySchema] = []
    images: list[ProductImageSchema] = []

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'parameters', 'price', 'categories', 'created_at', 'updated_at']


class ProductCreateSchema(ModelSchema):
    """Schema for Product creation."""
    category_ids: list[int] = []

    class Meta:
        model = Product
        fields = ['name', 'description', 'parameters', 'price']


class ProductUpdateSchema(ModelSchema):
    """Schema for Product update."""
    class Meta:
        model = Product
        fields = ['name', 'description', 'parameters', 'price']