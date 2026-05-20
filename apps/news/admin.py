"""Админка модуля новостей (django-unfold).

NewsTab — обычная справочная модель. NewsArticle — основная сущность с
prepopulated slug. NewsPageSettings — singleton с настройками страницы списка.
"""

from __future__ import annotations

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, reverse
from unfold.admin import ModelAdmin

from apps.shared.admin_mixins import RichTextAdminMixin
from .models import NewsArticle, NewsPageSettings, NewsTab


@admin.register(NewsTab, site=admin.site)
class NewsTabAdmin(ModelAdmin):
    list_display = ("title", "slug", "order")
    list_editable = ("order",)
    search_fields = ("title", "slug")
    ordering = ("order", "title")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(NewsArticle, site=admin.site)
class NewsArticleAdmin(RichTextAdminMixin, ModelAdmin):
    full_rich_fields = ("content",)
    list_display = ("title", "slug", "tab", "status", "date")
    list_filter = ("status", "tab")
    search_fields = ("title", "slug", "description")
    ordering = ("-date",)
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("tab", "picture")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Основное",
            {
                "fields": ("title", "slug", "status", "tab", "date"),
            },
        ),
        (
            "Контент",
            {
                "fields": ("description", "content", "picture"),
            },
        ),
        (
            "Даты",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


@admin.register(NewsPageSettings, site=admin.site)
class NewsPageSettingsAdmin(ModelAdmin):
    """Singleton настроек страницы списка новостей."""

    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Страница",
            {
                "fields": ("title", "description"),
            },
        ),
        (
            "Даты",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def has_add_permission(self, request, obj=None) -> bool:
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def get_urls(self):
        urls = super().get_urls()
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        custom = [
            path(
                "",
                self.admin_site.admin_view(self._singleton_redirect),
                name=f"{app_label}_{model_name}_changelist",
            ),
        ]
        return custom + urls

    def _singleton_redirect(self, request):
        obj = self.model.get_solo()
        return redirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[obj.pk],
            )
        )
