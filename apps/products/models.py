from django.db import models, transaction
from django.db.models import Q
from django.utils.text import slugify

from apps.shared.models import Image, TimeStampedModel
from apps.shared.services.sanitize import sanitize_html


class Category(TimeStampedModel):
    """Category model for products."""

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Название",
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name="Слаг",
        help_text="Уникальный идентификатор в URL /catalog/{slug}.",
    )
    poster = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Постер",
        help_text="Изображение плитки категории в каталоге.",
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductStatusChoices(models.TextChoices):
    """Статусы товара."""

    DRAFT = "draft", "Черновик"
    PUBLISHED = "published", "Опубликован"
    ARCHIVED = "archived", "Архивирован"


class ProductAvailabilityChoices(models.TextChoices):
    """Доступность товара."""

    IN_STOCK = "in_stock", "В наличии"
    OUT_OF_STOCK = "out_of_stock", "Нет в наличии"
    ON_REQUEST = "on_request", "Под заказ"


class Product(TimeStampedModel):
    """Product model with flexible parameters."""

    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Краткое описание",
        help_text="Текст карточки товара (без HTML).",
    )
    parameters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Гибкие параметры",
        help_text="Гибкие параметры: размер, цвет, объем и т.д.",
    )
    description_parameters = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Параметры описания",
        help_text=(
            "Список разделов описания товара. Формат: "
            '[{"title": "Общие характеристики", "parameters": "<p>HTML</p>"}].'
        ),
    )
    technical_specifications = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Технические характеристики",
        help_text=(
            "Список групп характеристик. Формат: "
            '[{"title": "Электрические параметры", '
            '"specifications": [{"label": "Напряжение", "value": "220 В"}]}].'
        ),
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Цена",
        help_text="Цена в рублях. В API округляется до целого.",
    )
    categories = models.ManyToManyField(
        Category,
        related_name="products",
        blank=True,
        verbose_name="Категории",
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Артикул",
        help_text="Артикул (SKU)",
    )
    brand = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Бренд",
    )
    status = models.CharField(
        max_length=20,
        choices=ProductStatusChoices.choices,
        default=ProductStatusChoices.DRAFT,
        verbose_name="Статус",
        help_text="Статус товара: черновик, опубликован, архивирован",
    )
    availability = models.CharField(
        max_length=20,
        choices=ProductAvailabilityChoices.choices,
        default=ProductAvailabilityChoices.IN_STOCK,
        verbose_name="Доступность",
        help_text="Доступность товара: в наличии, нет в наличии, под заказ",
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        self.description_parameters = _sanitize_description_parameters(
            self.description_parameters or []
        )
        super().save(*args, **kwargs)


def _sanitize_description_parameters(blocks):
    """Очистить HTML в parameters каждого блока через bleach."""
    cleaned = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        cleaned.append(
            {
                "title": str(block.get("title", "")),
                "parameters": sanitize_html(block.get("parameters", "")),
            }
        )
    return cleaned


class ProductImage(TimeStampedModel):
    """Изображение товара. Through-модель Product ↔ shared.Image."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Товар",
    )
    image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Изображение",
        help_text="Файл изображения из общего хранилища (с webp/avif производными).",
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name="Главное",
        help_text="Главное изображение карточки (poster). Только одно на товар.",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
        help_text="Порядок в галерее. Меньшее значение — раньше.",
    )

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"
        ordering = ["-is_primary", "order", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_primary=True),
                name="unique_primary_image_per_product",
                violation_error_message="Product already has a primary image.",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product.name} — image #{self.image_id}"

    def save(self, *args, **kwargs):
        """Гарантия одного primary на товар: при is_primary=True снимаем флаг с прочих."""
        if self.is_primary:
            with transaction.atomic():
                ProductImage.objects.filter(
                    product=self.product, is_primary=True
                ).exclude(pk=self.pk).update(is_primary=False)
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
