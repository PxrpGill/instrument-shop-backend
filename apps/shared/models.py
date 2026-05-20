from django.db import models


class TimeStampedModel(models.Model):
    """Абстрактная модель с метками времени создания и обновления."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        abstract = True


def _upload_source_desktop(instance: "Image", filename: str) -> str:
    return f"images/source/desktop/{filename}"


def _upload_source_mobile(instance: "Image", filename: str) -> str:
    return f"images/source/mobile/{filename}"


def _upload_derived(instance: "Image", filename: str) -> str:
    return f"images/derived/{filename}"


class Image(TimeStampedModel):
    """Универсальная модель изображения с автонарезкой webp/avif.

    Админ загружает один (или два — desktop + mobile) исходник.
    Сервис image_pipeline создаёт производные форматы webp/avif для каждого
    исходника. Контракт shared/picture описывает структуру отдачи на фронт.
    """

    alt_text = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Альтернативный текст",
        help_text="Описание изображения для accessibility и SEO.",
    )

    source_desktop = models.ImageField(
        upload_to=_upload_source_desktop,
        verbose_name="Исходник (desktop)",
        help_text="Основной исходный файл (jpg или png). Бекенд автоматически "
        "сгенерирует webp/avif производные.",
    )
    source_mobile = models.ImageField(
        upload_to=_upload_source_mobile,
        blank=True,
        null=True,
        verbose_name="Исходник (mobile)",
        help_text="Опциональный исходник для медиа max-width: 767px. "
        "Если не задан — фронт использует desktop-вариант.",
    )

    webp_desktop = models.FileField(
        upload_to=_upload_derived,
        blank=True,
        null=True,
        verbose_name="Производный WebP (desktop)",
        help_text="Генерируется автоматически после сохранения исходника.",
    )
    avif_desktop = models.FileField(
        upload_to=_upload_derived,
        blank=True,
        null=True,
        verbose_name="Производный AVIF (desktop)",
        help_text="Генерируется автоматически после сохранения исходника.",
    )
    webp_mobile = models.FileField(
        upload_to=_upload_derived,
        blank=True,
        null=True,
        verbose_name="Производный WebP (mobile)",
    )
    avif_mobile = models.FileField(
        upload_to=_upload_derived,
        blank=True,
        null=True,
        verbose_name="Производный AVIF (mobile)",
    )

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.alt_text or self.source_desktop.name
