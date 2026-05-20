"""Тесты сериализатора image_to_picture: соответствие контракту shared/picture."""

from __future__ import annotations

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage

from apps.shared.models import Image
from apps.shared.services.image_pipeline import regenerate_derivatives
from apps.shared.services.picture import image_to_picture


def _make_jpeg() -> SimpleUploadedFile:
    buffer = BytesIO()
    PILImage.new("RGB", (100, 100), color="blue").save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile("img.jpg", buffer.read(), content_type="image/jpeg")


def test_image_to_picture_returns_none_for_none_image():
    assert image_to_picture(None) is None


@pytest.mark.django_db
def test_image_to_picture_returns_only_original_before_conversion():
    image = Image.objects.create(source_desktop=_make_jpeg())

    picture = image_to_picture(image)

    assert picture is not None
    assert "original" in picture
    assert "webp" not in picture
    assert "avif" not in picture
    assert "src" in picture["original"]


@pytest.mark.django_db
def test_image_to_picture_includes_all_formats_after_conversion():
    image = Image.objects.create(source_desktop=_make_jpeg())
    regenerate_derivatives(image.pk)
    image.refresh_from_db()

    picture = image_to_picture(image)

    assert set(picture.keys()) == {"original", "webp", "avif"}
    for fmt in ("original", "webp", "avif"):
        assert "src" in picture[fmt]
        # mobile нет — не должно быть в выдаче
        assert "mobile" not in picture[fmt]


@pytest.mark.django_db
def test_image_to_picture_includes_mobile_when_source_mobile_set():
    image = Image.objects.create(
        source_desktop=_make_jpeg(),
        source_mobile=_make_jpeg(),
    )
    regenerate_derivatives(image.pk)
    image.refresh_from_db()

    picture = image_to_picture(image)

    for fmt in ("original", "webp", "avif"):
        assert "mobile" in picture[fmt]
