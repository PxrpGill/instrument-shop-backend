"""Admin configuration for products app using Unfold + django-nested-admin."""

import nested_admin
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.shared.admin_mixins import NestedRichTextInlineMixin
from apps.products.models import (
    Category,
    Product,
    ProductDescriptionBlock,
    ProductImage,
    ProductSpecGroup,
    ProductSpecItem,
)


class ProductImageInline(TabularInline):
    """Inline-редактор изображений товара."""

    model = ProductImage
    extra = 0
    fields = ("image", "is_primary", "order")
    ordering = ("-is_primary", "order")
    autocomplete_fields = ("image",)


class ProductDescriptionBlockInline(NestedRichTextInlineMixin, nested_admin.NestedStackedInline):
    """Блоки описания товара с CKEditor5."""

    model = ProductDescriptionBlock
    extra = 0
    fields = ("title", "content", "order")
    ordering = ("order",)
    simple_rich_fields = ("content",)
    verbose_name = "Блок описания"
    verbose_name_plural = "Блоки описания"


class ProductSpecItemInline(nested_admin.NestedTabularInline):
    """Строки характеристик внутри группы."""

    model = ProductSpecItem
    extra = 0
    fields = ("label", "value", "order")
    ordering = ("order",)
    verbose_name = "Характеристика"
    verbose_name_plural = "Характеристики"


class ProductSpecGroupInline(nested_admin.NestedStackedInline):
    """Группа характеристик с вложенными строками."""

    model = ProductSpecGroup
    extra = 0
    fields = ("title", "order")
    ordering = ("order",)
    inlines = [ProductSpecItemInline]
    verbose_name = "Группа характеристик"
    verbose_name_plural = "Технические характеристики"


@admin.register(Category, site=admin.site)
class CategoryAdmin(ModelAdmin):
    """Админ-панель для модели Category."""

    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    autocomplete_fields = ("poster",)


@admin.register(Product, site=admin.site)
class ProductAdmin(nested_admin.NestedModelAdmin, ModelAdmin):
    """Админ-панель для модели Product."""

    list_display = ("name", "brand", "price", "status", "availability", "created_at")
    list_filter = ("status", "availability", "categories", "brand")
    search_fields = ("name", "sku", "brand", "description")
    filter_horizontal = ("categories",)
    ordering = ("-created_at",)
    list_editable = ("status", "availability")
    inlines = [
        ProductImageInline,
        ProductDescriptionBlockInline,
        ProductSpecGroupInline,
    ]
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
            "Гибкие параметры",
            {
                "fields": ("parameters",),
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
