"""Админка модуля «Избранное» (django-unfold).

Для отладки — список с фильтрами по клиенту и товару, поиск по email.
Редактировать записи через админку обычно не нужно (создаются API).
"""

from __future__ import annotations

from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Favorite


@admin.register(Favorite, site=admin.site)
class FavoriteAdmin(ModelAdmin):
    list_display = ("customer", "product", "created_at")
    list_filter = ("created_at",)
    search_fields = ("customer__email", "product__name", "product__sku")
    autocomplete_fields = ("customer", "product")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
