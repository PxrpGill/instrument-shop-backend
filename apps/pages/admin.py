"""
Admin configuration for pages app using Unfold.
"""

from django.contrib import admin
from django.contrib.admin import TabularInline
from unfold.admin import ModelAdmin

from apps.pages.models import ContentBlock, Page, PageBlock


class PageBlockInline(TabularInline):
    """Inline для управления блоками на странице."""

    model = PageBlock
    extra = 1
    fields = ["block", "order"]
    autocomplete_fields = ["block"]
    ordering = ["order"]
    verbose_name = "Блок на странице"
    verbose_name_plural = "Блоки на странице"


@admin.register(Page, site=admin.site)
class PageAdmin(ModelAdmin):
    """Админ-панель для модели Page."""

    list_display = ("title", "slug", "block_count", "created_at")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PageBlockInline]
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Основное",
            {
                "fields": ("title", "slug"),
            },
        ),
        (
            "SEO",
            {
                "fields": ("meta_title", "meta_description", "og_image"),
            },
        ),
        (
            "Даты",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def block_count(self, obj) -> int:
        """Количество блоков на странице."""
        return obj.blocks.count()

    block_count.short_description = "Кол-во блоков"


@admin.register(ContentBlock, site=admin.site)
class ContentBlockAdmin(ModelAdmin):
    """Админ-панель для модели ContentBlock."""

    list_display = ("title", "block_type", "status", "created_at")
    list_filter = ("block_type", "status")
    search_fields = ("title",)
    list_editable = ("status",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Основное",
            {
                "fields": ("title", "block_type", "status"),
            },
        ),
        (
            "Содержимое",
            {
                "fields": ("content",),
                "classes": ("wide",),
                "description": "JSON-данные блока. Структура зависит от выбранного типа.",
            },
        ),
        (
            "Даты",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
