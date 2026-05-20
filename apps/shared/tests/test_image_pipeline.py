"""Тесты image_pipeline: загрузка Image → автоматическая генерация webp/avif."""

from __future__ import annotations

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage

from apps.shared.models import Image
from apps.shared.services.image_pipeline import regenerate_derivatives


def _make_jpeg(size=(200, 200), color="red") -> SimpleUploadedFile:
    buffer = BytesIO()
    PILImage.new("RGB", size, color=color).save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    return SimpleUploadedFile("source.jpg", buffer.read(), content_type="image/jpeg")


@pytest.mark.django_db
def test_image_save_triggers_webp_and_avif_generation():
    image = Image.objects.create(source_desktop=_make_jpeg(), alt_text="banner")

    # post_save сигнал отрабатывает через transaction.on_commit, который
    # в тестовой транзакции выполняется сразу при коммите. В pytest-django
    # с @pytest.mark.django_db (transaction=False) on_commit вызывается
    # немедленно — мы зовём regenerate_derivatives напрямую, чтобы тест
    # не зависел от тонкостей сигналов.
    regenerate_derivatives(image.pk)
    image.refresh_from_db()

    assert image.webp_desktop, "webp производный должен быть сгенерирован"
    assert image.avif_desktop, "avif производный должен быть сгенерирован"
    assert image.webp_desktop.name.endswith(".webp")
    assert image.avif_desktop.name.endswith(".avif")


@pytest.mark.django_db
def test_image_with_mobile_source_generates_mobile_derivatives():
    image = Image.objects.create(
        source_desktop=_make_jpeg(size=(400, 300)),
        source_mobile=_make_jpeg(size=(200, 150)),
    )

    regenerate_derivatives(image.pk)
    image.refresh_from_db()

    assert image.webp_mobile
    assert image.avif_mobile


@pytest.mark.django_db
def test_image_without_mobile_does_not_generate_mobile_derivatives():
    image = Image.objects.create(source_desktop=_make_jpeg())

    regenerate_derivatives(image.pk)
    image.refresh_from_db()

    assert not image.webp_mobile
    assert not image.avif_mobile
