from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Image


@receiver(post_save, sender=Image)
def regenerate_image_derivatives(sender, instance: Image, created: bool, **kwargs) -> None:
    """После сохранения Image — пересобрать webp/avif производные.

    Запускается после коммита транзакции, чтобы не блокировать админку
    и не дублировать запуск при ретраях. Сейчас работает синхронно —
    при росте нагрузки заменить на celery/django-q задачу.
    """
    from .services.image_pipeline import regenerate_derivatives

    transaction.on_commit(lambda: regenerate_derivatives(instance.pk))
