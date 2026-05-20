"""Сигналы каталога: инвалидация кеша при изменениях Product/Category/ProductImage."""

from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .catalog_controllers import (invalidate_catalog_cache,
                                  invalidate_product_cache)
from .models import Category, Product, ProductImage


@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def _product_changed(sender, instance: Product, **kwargs):
    invalidate_product_cache(instance.pk)
    invalidate_catalog_cache()


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def _category_changed(sender, instance: Category, **kwargs):
    invalidate_catalog_cache()


@receiver(post_save, sender=ProductImage)
@receiver(post_delete, sender=ProductImage)
def _product_image_changed(sender, instance: ProductImage, **kwargs):
    invalidate_product_cache(instance.product_id)
    invalidate_catalog_cache()
