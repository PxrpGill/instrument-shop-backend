"""Модели модуля новостей.

Структура определяется контрактами:
- contracts/news/list.json — список новостей с табами и пагинацией;
- contracts/news/single.json — страница одной новости;
- contracts/shared/news-card.json — карточка для списка.

Slug `all` — служебное значение фильтра «без таба». Реальная запись с таким
slug запрещена в админке (см. NewsTab.clean).
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.shared.models import Image, TimeStampedModel
from apps.shared.services.sanitize import sanitize_html


ALL_TAB_SLUG = "all"
ALL_TAB_TITLE = "Все новости"


class NewsTab(TimeStampedModel):
    """Таб фильтра для списка новостей.

    Slug `all` зарезервирован и подставляется в выдачу автоматически —
    создание такого таба запрещено.
    """

    slug = models.SlugField(
        max_length=64,
        unique=True,
        verbose_name="Slug",
        help_text="Идентификатор в URL/фильтре. Значение 'all' запрещено.",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Заголовок",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    class Meta:
        verbose_name = "Таб новостей"
        verbose_name_plural = "Табы новостей"
        ordering = ["order", "title"]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        if self.slug == ALL_TAB_SLUG:
            raise ValidationError(
                {"slug": "Slug 'all' зарезервирован для служебного таба."}
            )


class NewsArticleStatus(models.TextChoices):
    DRAFT = "draft", "Черновик"
    PUBLISHED = "published", "Опубликовано"


class NewsArticle(TimeStampedModel):
    """Статья новости. В публичный API попадают только статьи со статусом
    `published`.
    """

    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name="Slug",
        help_text="Уникальный идентификатор в URL /news/{slug}.",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Заголовок",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Тизер",
        help_text="Краткий plain-text для карточки и баннера single-страницы.",
    )
    content = models.TextField(
        blank=True,
        default="",
        verbose_name="Контент (HTML)",
        help_text="HTML, рендерится через dangerouslySetInnerHTML. "
        "Опасные теги вырезаются автоматически на save.",
    )
    date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата публикации",
        help_text="Отображается на фронте; ISO 8601 UTC в API.",
    )
    tab = models.ForeignKey(
        NewsTab,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
        verbose_name="Таб",
    )
    picture = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Изображение",
        help_text="Постер для карточки и баннера single-страницы.",
    )
    status = models.CharField(
        max_length=16,
        choices=NewsArticleStatus.choices,
        default=NewsArticleStatus.DRAFT,
        verbose_name="Статус",
    )

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["status", "-date"]),
            models.Index(fields=["tab", "status", "-date"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        self.content = sanitize_html(self.content)
        super().save(*args, **kwargs)


class NewsPageSettings(TimeStampedModel):
    """Singleton с настройками страницы списка новостей (title, description)."""

    title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Заголовок страницы",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Описание страницы",
    )

    class Meta:
        verbose_name = "Настройки страницы новостей"
        verbose_name_plural = "Настройки страницы новостей"

    def __str__(self) -> str:
        return "Настройки страницы новостей"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # pragma: no cover - защита от удаления
        pass

    @classmethod
    def get_solo(cls) -> "NewsPageSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
