"""Сигналы каталога: инвалидация кеша при изменениях Product/Category/ProductImage."""

from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .catalog_controllers import (invalidate_catalog_cache,
                                  invalidate_product_cache)
from .models import (
    Category,
    Product,
    ProductDescriptionBlock,
    ProductImage,
    ProductSpecGroup,
    ProductSpecItem,
)


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


@receiver(post_save, sender=ProductDescriptionBlock)
@receiver(post_delete, sender=ProductDescriptionBlock)
def _description_block_changed(sender, instance: ProductDescriptionBlock, **kwargs):
    invalidate_product_cache(instance.product_id)


@receiver(post_save, sender=ProductSpecGroup)
@receiver(post_delete, sender=ProductSpecGroup)
def _spec_group_changed(sender, instance: ProductSpecGroup, **kwargs):
    invalidate_product_cache(instance.product_id)


@receiver(post_save, sender=ProductSpecItem)
@receiver(post_delete, sender=ProductSpecItem)
def _spec_item_changed(sender, instance: ProductSpecItem, **kwargs):
    invalidate_product_cache(instance.group.product_id)
