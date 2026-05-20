"""Конвертер исходных изображений Image в webp/avif производные.

Запускается из signals.post_save через transaction.on_commit. Сейчас работает
синхронно — при росте нагрузки заменить на celery/django-q задачу,
интерфейс regenerate_derivatives() менять не понадобится.
"""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from typing import Optional

import pillow_avif  # noqa: F401  # регистрирует AVIF-плагин в Pillow
from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile
from PIL import Image as PILImage

logger = logging.getLogger(__name__)

WEBP_QUALITY = 85
AVIF_QUALITY = 70


def regenerate_derivatives(image_id: int) -> None:
    """Главная точка входа из сигнала.

    Загружает Image по id, генерирует недостающие webp/avif для desktop и
    mobile исходников, сохраняет одной операцией update_fields.
    """
    from apps.shared.models import Image

    image = Image.objects.filter(pk=image_id).first()
    if image is None:
        return

    updated_fields: list[str] = []

    desktop_webp = _convert(image.source_desktop, "webp")
    if desktop_webp is not None:
        _attach(image, "webp_desktop", desktop_webp, updated_fields)

    desktop_avif = _convert(image.source_desktop, "avif")
    if desktop_avif is not None:
        _attach(image, "avif_desktop", desktop_avif, updated_fields)

    if image.source_mobile:
        mobile_webp = _convert(image.source_mobile, "webp")
        if mobile_webp is not None:
            _attach(image, "webp_mobile", mobile_webp, updated_fields)

        mobile_avif = _convert(image.source_mobile, "avif")
        if mobile_avif is not None:
            _attach(image, "avif_mobile", mobile_avif, updated_fields)

    if updated_fields:
        Image.objects.filter(pk=image.pk).update(
            **{field: getattr(image, field) for field in updated_fields}
        )


def _convert(source: FieldFile, target_format: str) -> Optional[ContentFile]:
    """Конвертирует source FieldFile в формат webp или avif.

    Возвращает ContentFile, готовый к присваиванию ImageField/FileField.
    Возвращает None, если конверсия не удалась — это не фатальная ошибка,
    отсутствие производного формата корректно обрабатывается контрактом
    shared/picture (фронт fallback'ом возьмёт original).
    """
    if not source:
        return None

    try:
        with PILImage.open(source.path) as pil_image:
            buffer = BytesIO()
            save_kwargs = _save_kwargs(target_format)
            pil_image.save(buffer, format=target_format.upper(), **save_kwargs)
            buffer.seek(0)
            new_name = f"{Path(source.name).stem}.{target_format}"
            return ContentFile(buffer.read(), name=new_name)
    except Exception:
        logger.exception(
            "Failed to convert %s to %s", source.name, target_format
        )
        return None


def _save_kwargs(target_format: str) -> dict:
    if target_format == "webp":
        return {"quality": WEBP_QUALITY, "method": 6}
    if target_format == "avif":
        return {"quality": AVIF_QUALITY}
    return {}


def _attach(image, field_name: str, content: ContentFile, tracked: list[str]) -> None:
    field: FieldFile = getattr(image, field_name)
    field.save(content.name, content, save=False)
    tracked.append(field_name)
