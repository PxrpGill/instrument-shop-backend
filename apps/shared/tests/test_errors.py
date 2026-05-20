"""Тесты BusinessError и формата ответов error-handler'а."""

from __future__ import annotations

import pytest
from ninja import NinjaAPI, Schema
from ninja.testing import TestClient

from apps.shared.errors import BusinessError, ErrorCode, not_found
from apps.shared.exception_handlers import register_error_handlers


class _Payload(Schema):
    email: str
    age: int


@pytest.fixture
def api_client():
    api = NinjaAPI()
    register_error_handlers(api)

    @api.get("/raise-business")
    def raise_business(request):
        raise not_found("Тест 404")

    @api.get("/raise-internal")
    def raise_internal(request):
        raise RuntimeError("boom")

    @api.post("/validate")
    def validate(request, payload: _Payload):
        return {"ok": True}

    return TestClient(api)


def test_business_error_to_payload_contains_code_and_message():
    err = BusinessError("CUSTOM", "msg", status=400)
    payload = err.to_payload()
    assert payload == {"error": {"code": "CUSTOM", "message": "msg"}}


def test_business_error_to_payload_includes_fields_when_present():
    err = BusinessError("X", "msg", status=422, fields={"email": ["bad"]})
    payload = err.to_payload()
    assert payload["error"]["fields"] == {"email": ["bad"]}


def test_business_error_handler_returns_correct_status(api_client):
    response = api_client.get("/raise-business")
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": ErrorCode.NOT_FOUND, "message": "Тест 404"}
    }


def test_unhandled_exception_returns_500_internal_error(api_client):
    response = api_client.get("/raise-internal")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == ErrorCode.INTERNAL_ERROR


def test_validation_error_returns_422_with_fields(api_client):
    response = api_client.post("/validate", json={"email": "bad"})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == ErrorCode.VALIDATION_ERROR
    assert "age" in body["error"]["fields"]
