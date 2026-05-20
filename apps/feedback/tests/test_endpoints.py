"""Тесты POST /api/feedback (contracts/feedback/submit.json)."""

from __future__ import annotations

import pytest
from django.core.cache import cache
from django.test import override_settings

from apps.feedback.models import FeedbackMessage

pytestmark = pytest.mark.django_db

URL = "/feedback"


@pytest.fixture(autouse=True)
def _clear_cache():
    """django-ratelimit держит счётчики в Redis — чистим до и после."""
    cache.clear()
    yield
    cache.clear()


def _valid_payload(**overrides) -> dict:
    payload = {
        "full_name": "Иван Иванов",
        "email": "ivan@example.com",
        "phone": "+7 (999) 123-45-67",
        "message": "Подскажите наличие дрели Metabo SBE 650",
        "agreement": True,
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_submit_success_returns_201(client):
    response = client.post(URL, json=_valid_payload())
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["message"].startswith("Ваше обращение принято")

    created = FeedbackMessage.objects.get(id=body["id"])
    assert created.full_name == "Иван Иванов"
    assert created.email == "ivan@example.com"
    assert created.phone == "+7 (999) 123-45-67"
    assert created.message.startswith("Подскажите")
    assert created.processed_at is None


@pytest.mark.parametrize(
    "phone",
    [
        "+7 (999) 123-45-67",
        "+79991234567",
        "8 999 123 45 67",
        "8-999-123-45-67",
    ],
)
def test_submit_accepts_various_ru_phone_formats(client, phone):
    response = client.post(URL, json=_valid_payload(phone=phone))
    assert response.status_code == 201


# ---------------------------------------------------------------------------
# Validation (422)
# ---------------------------------------------------------------------------


def _assert_validation_error(response, field: str):
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert field in body["error"]["fields"]


def test_submit_rejects_full_name_with_digits(client):
    response = client.post(URL, json=_valid_payload(full_name="Иван 123"))
    _assert_validation_error(response, "full_name")


def test_submit_rejects_full_name_with_double_spaces(client):
    response = client.post(URL, json=_valid_payload(full_name="Иван  Иванов"))
    _assert_validation_error(response, "full_name")


def test_submit_rejects_short_full_name(client):
    response = client.post(URL, json=_valid_payload(full_name="И"))
    _assert_validation_error(response, "full_name")


def test_submit_rejects_invalid_email(client):
    response = client.post(URL, json=_valid_payload(email="not-an-email"))
    _assert_validation_error(response, "email")


def test_submit_rejects_invalid_phone(client):
    response = client.post(URL, json=_valid_payload(phone="123"))
    _assert_validation_error(response, "phone")


def test_submit_rejects_empty_message(client):
    response = client.post(URL, json=_valid_payload(message=""))
    _assert_validation_error(response, "message")


def test_submit_rejects_too_long_message(client):
    response = client.post(URL, json=_valid_payload(message="a" * 2001))
    _assert_validation_error(response, "message")


def test_submit_requires_agreement_true(client):
    response = client.post(URL, json=_valid_payload(agreement=False))
    _assert_validation_error(response, "agreement")


# ---------------------------------------------------------------------------
# Rate limit (429)
# ---------------------------------------------------------------------------


@override_settings(RATELIMIT_ENABLE=True)
def test_submit_returns_429_after_limit(client):
    """6-й запрос за час с одного IP должен получить 429 в формате shared/error."""
    payload = _valid_payload()
    for _ in range(5):
        response = client.post(URL, json=payload)
        assert response.status_code == 201, response.json()

    response = client.post(URL, json=payload)
    assert response.status_code == 429
    body = response.json()
    assert body["error"]["code"] == "RATE_LIMITED"
