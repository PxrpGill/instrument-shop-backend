from ninja import ModelSchema
from .models import Category, Product


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


class ProductSchema(ModelSchema):
    """Schema for Product output."""
    categories: list[CategorySchema] = []

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