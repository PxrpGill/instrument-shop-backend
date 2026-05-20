"""Админка обратной связи (django-unfold).

Менеджеры читают входящие обращения, фильтруют по статусу обработки и дате,
ищут по имени/email/телефону, при необходимости отмечают «обработано».
"""

from __future__ import annotations

from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin

from .models import FeedbackMessage


@admin.register(FeedbackMessage, site=admin.site)
class FeedbackMessageAdmin(ModelAdmin):
    list_display = ("full_name", "email", "phone", "is_processed", "created_at")
    list_filter = ("processed_at", "created_at")
    search_fields = ("full_name", "email", "phone", "message")
    readonly_fields = ("created_at", "ip_address")
    ordering = ("-created_at",)
    actions = ["mark_as_processed", "mark_as_unprocessed"]
    fieldsets = (
        (
            "Контакты",
            {"fields": ("full_name", "email", "phone")},
        ),
        (
            "Сообщение",
            {"fields": ("message",)},
        ),
        (
            "Служебное",
            {
                "fields": ("ip_address", "created_at", "processed_at"),
            },
        ),
    )

    @admin.display(boolean=True, description="Обработано")
    def is_processed(self, obj: FeedbackMessage) -> bool:
        return obj.is_processed

    @admin.action(description="Отметить как обработанные")
    def mark_as_processed(self, request, queryset):
        queryset.update(processed_at=timezone.now())

    @admin.action(description="Снять отметку «обработано»")
    def mark_as_unprocessed(self, request, queryset):
        queryset.update(processed_at=None)
