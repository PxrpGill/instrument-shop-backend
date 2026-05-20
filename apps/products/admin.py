"""Admin configuration for products app using Unfold."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.products.models import Category, Product, ProductImage


class ProductImageInline(TabularInline):
    """Inline-редактор изображений товара."""

    model = ProductImage
    extra = 0
    fields = ("image", "is_primary", "order")
    ordering = ("-is_primary", "order")
    autocomplete_fields = ("image",)


@admin.register(Category, site=admin.site)
class CategoryAdmin(ModelAdmin):
    """Админ-панель для модели Category."""

    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    autocomplete_fields = ("poster",)


@admin.register(Product, site=admin.site)
class ProductAdmin(ModelAdmin):
    """Админ-панель для модели Product."""

    list_display = ("name", "brand", "price", "status", "availability", "created_at")
    list_filter = ("status", "availability", "categories", "brand")
    search_fields = ("name", "sku", "brand", "description")
    filter_horizontal = ("categories",)
    ordering = ("-created_at",)
    list_editable = ("status", "availability")
    inlines = [ProductImageInline]
    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "name",
                    "sku",
                    "brand",
                    "description",
                    "categories",
                ),
            },
        ),
        (
            "Цена и доступность",
            {"fields": ("price", "status", "availability")},
        ),
        (
            "Параметры карточки",
            {
                "fields": (
                    "parameters",
                    "description_parameters",
                    "technical_specifications",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ProductImage, site=admin.site)
class ProductImageAdmin(ModelAdmin):
    """Админ-панель для модели ProductImage."""

    list_display = ("product", "image", "is_primary", "order", "created_at")
    list_filter = ("is_primary",)
    search_fields = ("product__name",)
    ordering = ("-is_primary", "order")
    autocomplete_fields = ("product", "image")
