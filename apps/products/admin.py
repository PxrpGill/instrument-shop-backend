"""Admin configuration for products app using Unfold."""

from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from apps.shared.admin_mixins import RichTextInlineMixin
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


class ProductDescriptionBlockInline(RichTextInlineMixin, StackedInline):
    """Блоки описания товара с CKEditor5."""

    model = ProductDescriptionBlock
    extra = 0
    fields = ("title", "content", "order")
    ordering = ("order",)
    simple_rich_fields = ("content",)
    verbose_name = "Блок описания"
    verbose_name_plural = "Блоки описания"


class ProductSpecGroupInline(TabularInline):
    """Группы характеристик на товаре — строки редактируются на отдельной странице группы."""

    model = ProductSpecGroup
    extra = 0
    fields = ("title", "order")
    ordering = ("order",)
    show_change_link = True
    verbose_name = "Группа характеристик"
    verbose_name_plural = "Технические характеристики"


class ProductSpecItemInline(TabularInline):
    """Строки характеристик внутри группы."""

    model = ProductSpecItem
    extra = 0
    fields = ("label", "value", "order")
    ordering = ("order",)
    verbose_name = "Характеристика"
    verbose_name_plural = "Характеристики"


@admin.register(Category, site=admin.site)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    autocomplete_fields = ("poster",)


@admin.register(Product, site=admin.site)
class ProductAdmin(ModelAdmin):
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


@admin.register(ProductSpecGroup, site=admin.site)
class ProductSpecGroupAdmin(ModelAdmin):
    """Группа характеристик — редактируется отдельной страницей (как HomePageShowcase)."""

    list_display = ("title", "product", "order")
    list_filter = ("product",)
    search_fields = ("title", "product__name")
    ordering = ("product", "order")
    inlines = [ProductSpecItemInline]


@admin.register(ProductImage, site=admin.site)
class ProductImageAdmin(ModelAdmin):
    list_display = ("product", "image", "is_primary", "order", "created_at")
    list_filter = ("is_primary",)
    search_fields = ("product__name",)
    ordering = ("-is_primary", "order")
    autocomplete_fields = ("product", "image")
