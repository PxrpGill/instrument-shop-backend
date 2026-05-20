"""Admin для общих компонентов: универсальная Image с автонарезкой."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.shared.models import Image


@admin.register(Image, site=admin.site)
class ImageAdmin(ModelAdmin):
    """Админка универсального изображения.

    Админ загружает source_desktop (обязательно) и опционально source_mobile.
    Производные webp/avif генерируются автоматически после save (см. signals).
    """

    list_display = ("__str__", "alt_text", "created_at")
    search_fields = ("alt_text", "source_desktop")
    readonly_fields = (
        "webp_desktop",
        "avif_desktop",
        "webp_mobile",
        "avif_mobile",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        ("Основное", {"fields": ("alt_text", "source_desktop", "source_mobile")}),
        (
            "Производные (генерируются автоматически)",
            {
                "fields": (
                    "webp_desktop",
                    "avif_desktop",
                    "webp_mobile",
                    "avif_mobile",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Метки времени", {"fields": ("created_at", "updated_at")}),
    )
