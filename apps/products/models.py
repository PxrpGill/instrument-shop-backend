from django.db import models, transaction
from django.db.models import Q
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    """Abstract base model with created_at and updated_at timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    """Category model for products."""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)

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

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Гибкие параметры: размер, цвет, объем и т.д.",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    categories = models.ManyToManyField(
        Category,
        related_name="products",
        blank=True,
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        help_text="Артикул (SKU)",
    )
    brand = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Бренд товара",
    )
    status = models.CharField(
        max_length=20,
        choices=ProductStatusChoices.choices,
        default=ProductStatusChoices.DRAFT,
        help_text="Статус товара: черновик, опубликован, архивирован",
    )
    availability = models.CharField(
        max_length=20,
        choices=ProductAvailabilityChoices.choices,
        default=ProductAvailabilityChoices.IN_STOCK,
        help_text="Доступность товара: в наличии, нет в наличии, под заказ",
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class ProductImage(TimeStampedModel):
    """Image model for products."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(
        max_length=255, blank=True, help_text="Альтернативный текст для изображения"
    )
    is_primary = models.BooleanField(
        default=False, help_text="Установить как основное изображение товара"
    )

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"
        ordering = ["-is_primary", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_primary=True),
                name="unique_primary_image_per_product",
                violation_error_message="Product already has a primary image.",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.image.name}"

    def save(self, *args, **kwargs):
        """
        Override save to ensure only one primary image per product.

        When setting is_primary=True, all other images for this product
        will have is_primary set to False.
        """
        if self.is_primary:
            # Use transaction to ensure consistency
            with transaction.atomic():
                # Set all other images for this product to not primary
                ProductImage.objects.filter(
                    product=self.product, is_primary=True
                ).exclude(pk=self.pk).update(is_primary=False)
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
