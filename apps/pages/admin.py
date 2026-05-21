"""Админка публичных страниц (django-unfold).

Все страницы — singleton'ы (pk=1). Кнопки «Добавить» и «Удалить» скрыты,
существующая запись создаётся лениво при первом обращении через get_solo().
LegalDocument — три фиксированные записи (создаются вручную через сидинг
или вручную в админке, после чего add/delete блокируются).
"""

from __future__ import annotations

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, reverse
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from apps.shared.admin_mixins import RichTextAdminMixin, RichTextInlineMixin

from .models import (
    AboutUsPage,
    BuyersPage,
    FeedbackPage,
    HomePage,
    HomePageReview,
    HomePageShowcase,
    HomePageShowcaseProduct,
    LegalDocument,
    LegalDocumentSlugChoices,
    LegalSection,
)


class SingletonAdminMixin:
    """Свойства, общие для singleton-страниц.

    - убираем «Добавить» и «Удалить»,
    - чейнджлист подменяется редиректом на форму единственной записи.
    """

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
        # Перекрываем стандартный changelist кастомным редиректом — он первым.
        return custom + urls

    def _singleton_redirect(self, request):
        obj = self.model.get_solo()
        return redirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[obj.pk],
            )
        )


# =============================================================================
# Home page
# =============================================================================


class HomePageReviewInline(TabularInline):
    model = HomePageReview
    extra = 0
    fields = ("review", "order")
    autocomplete_fields = ("review",)
    ordering = ("order",)
    verbose_name = "Отзыв"
    verbose_name_plural = "Отзывы на главной"


class HomePageShowcaseProductInline(TabularInline):
    model = HomePageShowcaseProduct
    extra = 0
    fields = ("product", "order")
    autocomplete_fields = ("product",)
    ordering = ("order",)
    verbose_name = "Товар"
    verbose_name_plural = "Товары в группе"


@admin.register(HomePageShowcase, site=admin.site)
class HomePageShowcaseAdmin(ModelAdmin):
    """Группа товаров на главной. Редактируется отдельной страницей,
    потому что Django не поддерживает nested-inline.
    """

    list_display = ("title", "home_page", "order")
    list_filter = ("home_page",)
    search_fields = ("title",)
    ordering = ("order",)
    inlines = [HomePageShowcaseProductInline]


class HomePageShowcaseInline(TabularInline):
    """Внутри HomePageAdmin показываем только список групп — переход на
    редактирование товаров идёт по ссылке на отдельный change-view группы.
    """

    model = HomePageShowcase
    extra = 0
    fields = ("title", "order")
    show_change_link = True
    ordering = ("order",)
    verbose_name = "Группа витрины"
    verbose_name_plural = "Группы витрины"


@admin.register(HomePage, site=admin.site)
class HomePageAdmin(RichTextAdminMixin, SingletonAdminMixin, ModelAdmin):
    simple_rich_fields = ("hero_description", "news_cta_description")
    full_rich_fields = ("about_content",)
    inlines = [HomePageReviewInline, HomePageShowcaseInline]
    autocomplete_fields = ("hero_poster", "about_poster", "news_cta_poster")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Hero",
            {
                "fields": (
                    "hero_title",
                    "hero_description",
                    "hero_button_title",
                    "hero_button_href",
                    "hero_poster",
                ),
            },
        ),
        (
            "О компании",
            {
                "fields": ("about_title", "about_content", "about_poster"),
            },
        ),
        (
            "Отзывы",
            {
                "fields": ("reviews_title",),
            },
        ),
        (
            "Витрина",
            {
                "fields": (
                    "showcase_title",
                    "showcase_button_title",
                    "showcase_button_href",
                ),
            },
        ),
        (
            "Новости (CTA)",
            {
                "fields": (
                    "news_cta_title",
                    "news_cta_description",
                    "news_cta_button_title",
                    "news_cta_button_href",
                    "news_cta_poster",
                ),
            },
        ),
        (
            "Даты",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


# =============================================================================
# About-us / Buyers
# =============================================================================


class _BannerPageAdmin(RichTextAdminMixin, SingletonAdminMixin, ModelAdmin):
    simple_rich_fields = ("banner_description",)
    full_rich_fields = ("content",)
    autocomplete_fields = ("banner_poster",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Баннер",
            {
                "fields": ("banner_title", "banner_description", "banner_poster"),
            },
        ),
        (
            "Контент",
            {
                "fields": ("content",),
            },
        ),
        (
            "Даты",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


@admin.register(AboutUsPage, site=admin.site)
class AboutUsPageAdmin(_BannerPageAdmin):
    pass


@admin.register(BuyersPage, site=admin.site)
class BuyersPageAdmin(_BannerPageAdmin):
    pass


# =============================================================================
# Feedback
# =============================================================================


@admin.register(FeedbackPage, site=admin.site)
class FeedbackPageAdmin(RichTextAdminMixin, SingletonAdminMixin, ModelAdmin):
    simple_rich_fields = ("section_description", "news_cta_description")
    autocomplete_fields = ("news_cta_poster",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Секция",
            {
                "fields": ("section_title", "section_description"),
            },
        ),
        (
            "Новости (CTA)",
            {
                "fields": (
                    "news_cta_title",
                    "news_cta_description",
                    "news_cta_button_title",
                    "news_cta_button_href",
                    "news_cta_poster",
                ),
            },
        ),
        (
            "Даты",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


# =============================================================================
# Legal documents
# =============================================================================


class LegalSectionInline(RichTextInlineMixin, StackedInline):
    model = LegalSection
    extra = 0
    fields = ("anchor_id", "title", "content", "order")
    ordering = ("order",)
    simple_rich_fields = ("content",)


@admin.register(LegalDocument, site=admin.site)
class LegalDocumentAdmin(ModelAdmin):
    list_display = ("slug", "title", "last_updated")
    search_fields = ("title",)
    ordering = ("slug",)
    inlines = [LegalSectionInline]

    def has_add_permission(self, request) -> bool:
        existing = set(LegalDocument.objects.values_list("slug", flat=True))
        all_slugs = {choice for choice, _ in LegalDocumentSlugChoices.choices}
        return bool(all_slugs - existing)

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
