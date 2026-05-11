from django.db import models
from django.utils.text import slugify

from apps.products.models import TimeStampedModel


class BlockStatusChoices(models.TextChoices):
    """Статусы контентного блока."""

    DRAFT = "draft", "Черновик"
    PUBLISHED = "published", "Опубликован"


class BlockTypeChoices(models.TextChoices):
    """Типы контентных блоков."""

    HERO = "hero", "Hero/CTA блок"
    TEXT = "text", "Текст"
    FAQ = "faq", "FAQ (вопросы-ответы)"
    FEATURES = "features", "Преимущества"
    GALLERY = "gallery", "Галерея"
    REVIEWS = "reviews", "Отзывы"
    BANNER = "banner", "Баннер"
    VIDEO = "video", "Видео"
    STATISTICS = "statistics", "Статистика/Цифры"
    CONTACTS = "contacts", "Контакты"


# =============================================================================
# Content Block Templates
# =============================================================================
# Каждый тип блока ожидает определённую структуру JSON в поле `content`:
#
# hero:
#   {title, subtitle, text, button_text, button_url, background_image, background_color}
# text:
#   {content, alignment}
# faq:
#   {items: [{question, answer}]}
# features:
#   {items: [{icon, title, description}]}
# gallery:
#   {images: [{image, alt_text}]}
# reviews:
#   {items: [{author_name, author_title, text, avatar, rating}]}
# banner:
#   {image, link_url, link_text, alt_text}
# video:
#   {embed_url, title, description}
# statistics:
#   {items: [{number, label, prefix, suffix}]}
# contacts:
#   {address, phone, email, working_hours, map_coordinates}


class ContentBlock(TimeStampedModel):
    """Модель контентного блока.

    Блок хранит typed-контент в JSONField. Тип блока определяет,
    как фронтенд будет интерпретировать данные.
    Блок может быть переиспользован на разных страницах.
    """

    title = models.CharField(
        max_length=255,
        verbose_name="Название",
        help_text="Внутреннее название блока для админки",
    )
    block_type = models.CharField(
        max_length=20,
        choices=BlockTypeChoices.choices,
        verbose_name="Тип блока",
        help_text="Выберите тип контентного блока",
    )
    content = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Содержимое блока",
        help_text="Данные блока в формате JSON. Структура зависит от типа блока.",
    )
    status = models.CharField(
        max_length=20,
        choices=BlockStatusChoices.choices,
        default=BlockStatusChoices.DRAFT,
        verbose_name="Статус",
        help_text="Черновик — блок не отображается на сайте. Опубликован — блок виден на сайте.",
    )

    class Meta:
        verbose_name = "Блок контента"
        verbose_name_plural = "Блоки контента"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_block_type_display()}: {self.title}"


class Page(TimeStampedModel):
    """Модель страницы сайта.

    Страница объединяет контентные блоки в определённом порядке
    и содержит SEO-метаданные для поисковой оптимизации.
    """

    title = models.CharField(
        max_length=255,
        verbose_name="Заголовок",
        help_text="Заголовок страницы",
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name="URL-идентификатор",
        help_text="Уникальный идентификатор для URL. Автоматически генерируется из заголовка.",
    )
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Meta Title",
        help_text="SEO-заголовок для поисковых систем. Если не указан, используется заголовок страницы.",
    )
    meta_description = models.TextField(
        blank=True,
        default="",
        verbose_name="Meta Description",
        help_text="SEO-описание для поисковых систем.",
    )
    og_image = models.ImageField(
        upload_to="pages/og/",
        blank=True,
        null=True,
        verbose_name="OG изображение",
        help_text="Изображение для предпросмотра при отправке ссылки в соцсетях.",
    )
    blocks = models.ManyToManyField(
        ContentBlock,
        through="PageBlock",
        through_fields=("page", "block"),
        related_name="pages",
        verbose_name="Блоки",
        help_text="Контентные блоки, отображаемые на этой странице.",
    )

    class Meta:
        verbose_name = "Страница"
        verbose_name_plural = "Страницы"
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class PageBlock(TimeStampedModel):
    """Промежуточная модель для связи Page и ContentBlock с сортировкой."""

    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="page_blocks",
        verbose_name="Страница",
    )
    block = models.ForeignKey(
        ContentBlock,
        on_delete=models.CASCADE,
        related_name="page_blocks",
        verbose_name="Блок",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
        help_text="Порядок отображения блока на странице.",
    )

    class Meta:
        verbose_name = "Блок на странице"
        verbose_name_plural = "Блоки на странице"
        ordering = ["order"]
        unique_together = [["page", "block"]]

    def __str__(self) -> str:
        return f"{self.page.title} → {self.block.title} (порядок: {self.order})"
