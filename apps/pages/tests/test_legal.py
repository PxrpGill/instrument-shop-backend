"""Тесты юридических документов (/api/pages/legal/{slug})."""

from __future__ import annotations

import pytest

from apps.pages.models import LegalDocument, LegalSection

pytestmark = pytest.mark.django_db


def test_legal_404_for_unknown_slug(client):
    response = client.get("/pages/legal/unknown")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"


def test_legal_document_with_sections_ordered(client):
    doc = LegalDocument.objects.create(
        slug="privacy-policy",
        title="Политика конфиденциальности",
        last_updated="01.01.2025",
    )
    LegalSection.objects.create(
        document=doc,
        anchor_id="data-collected",
        title="Какие данные мы собираем",
        content="Текст второго раздела.",
        order=2,
    )
    LegalSection.objects.create(
        document=doc,
        anchor_id="general",
        title="Общие положения",
        content="Абзац 1.\n\nАбзац 2.",
        order=1,
    )

    data = client.get("/pages/legal/privacy-policy").json()
    assert data["title"] == "Политика конфиденциальности"
    assert data["last_updated"] == "01.01.2025"
    assert [s["id"] for s in data["sections"]] == ["general", "data-collected"]
    assert data["sections"][0]["content"] == "Абзац 1.\n\nАбзац 2."
