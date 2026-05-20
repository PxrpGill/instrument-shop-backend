"""Сериализатор Image → PictureSchema по контракту shared/picture."""

from __future__ import annotations

from typing import Optional

from django.db.models.fields.files import FieldFile
from django.http import HttpRequest

from apps.shared.models import Image


def image_to_picture(
    image: Optional[Image],
    request: Optional[HttpRequest] = None,
) -> Optional[dict]:
    """Преобразовать Image в dict, соответствующий контракту shared/picture.

    Возвращает None, если image не задан (опциональное поле — секцию `poster`
    или `og_image` родительский сериализатор просто пропустит). Если у image
    нет ни одного валидного URL, тоже None.

    Опциональные подэлементы (mobile, отсутствующие форматы) **не включаются**
    в dict — фронту проще проверять `if picture.webp` без `if picture.webp.src`.
    """
    if image is None:
        return None

    original = _build_variant(
        desktop=image.source_desktop,
        mobile=image.source_mobile,
        request=request,
    )
    webp = _build_variant(
        desktop=image.webp_desktop,
        mobile=image.webp_mobile,
        request=request,
    )
    avif = _build_variant(
        desktop=image.avif_desktop,
        mobile=image.avif_mobile,
        request=request,
    )

    result: dict = {}
    if original is not None:
        result["original"] = original
    if webp is not None:
        result["webp"] = webp
    if avif is not None:
        result["avif"] = avif

    return result or None


def _build_variant(
    desktop: FieldFile,
    mobile: FieldFile,
    request: Optional[HttpRequest],
) -> Optional[dict]:
    variant: dict = {}
    if desktop:
        variant["src"] = _absolute_url(desktop, request)
    if mobile:
        variant["mobile"] = _absolute_url(mobile, request)
    return variant or None


def _absolute_url(field: FieldFile, request: Optional[HttpRequest]) -> str:
    url = field.url
    if request is None:
        return url
    return request.build_absolute_uri(url)
