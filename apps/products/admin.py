"""
Admin configuration for products app using Unfold.
"""

from unfold.admin import ModelAdmin
from django.contrib import admin
from apps.products.models import Category, Product, ProductImage


@admin.register(Category, site=admin.site)
class CategoryAdmin(ModelAdmin):
    """Админ-панель для модели Category."""

    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Product, site=admin.site)
class ProductAdmin(ModelAdmin):
    """Админ-панель для модели Product."""

    list_display = ('name', 'brand', 'price', 'status', 'availability', 'created_at')
    list_filter = ('status', 'availability', 'categories', 'brand')
    search_fields = ('name', 'sku', 'brand', 'description')
    filter_horizontal = ('categories',)
    ordering = ('-created_at',)
    list_editable = ('status', 'availability')


@admin.register(ProductImage, site=admin.site)
class ProductImageAdmin(ModelAdmin):
    """Админ-панель для модели ProductImage."""

    list_display = ('product', 'alt_text', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'product')
    search_fields = ('product__name', 'alt_text')
    ordering = ('-is_primary', '-created_at')
