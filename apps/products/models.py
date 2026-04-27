from django.db import models
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
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductStatusChoices(models.TextChoices):
    """Product status choices."""

    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class ProductAvailabilityChoices(models.TextChoices):
    """Product availability choices."""

    IN_STOCK = "in_stock", "In Stock"
    OUT_OF_STOCK = "out_of_stock", "Out of Stock"
    ON_REQUEST = "on_request", "On Request"


class Product(TimeStampedModel):
    """Product model with flexible parameters."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible parameters like size, color, volume, etc.",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
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
        help_text="Stock keeping unit ( SKU)",
    )
    brand = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Product brand",
    )
    status = models.CharField(
        max_length=20,
        choices=ProductStatusChoices.choices,
        default=ProductStatusChoices.DRAFT,
        help_text="Product status: draft, published, archived",
    )
    availability = models.CharField(
        max_length=20,
        choices=ProductAvailabilityChoices.choices,
        default=ProductAvailabilityChoices.IN_STOCK,
        help_text="Product availability: in_stock, out_of_stock, on_request",
    )

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
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
        max_length=255, blank=True, help_text="Alternative text for the image"
    )
    is_primary = models.BooleanField(
        default=False, help_text="Set as primary image for the product"
    )

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ["-is_primary", "-created_at"]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.image.name}"
