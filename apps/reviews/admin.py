from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.reviews.models import Review


@admin.register(Review, site=admin.site)
class ReviewAdmin(ModelAdmin):
    """Админ-панель отзывов покупателей."""

    list_display = ("title", "author_full_name", "grade", "is_published", "created_at")
    list_filter = ("grade", "is_published")
    search_fields = ("title", "author_full_name", "description")
    list_editable = ("is_published",)
    autocomplete_fields = ("author_icon",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Основное",
            {
                "fields": ("title", "description", "grade", "is_published"),
            },
        ),
        (
            "Автор",
            {
                "fields": ("author_full_name", "author_icon"),
            },
        ),
        (
            "Даты",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
