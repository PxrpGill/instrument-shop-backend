"""Регистрация exception-handler'ов на NinjaAPI.

Все 4xx/5xx ошибки должны возвращать JSON формата shared/error.json
(см. apps.shared.errors.BusinessError.to_payload). Это позволяет фронту
обрабатывать ошибки единообразно вне зависимости от источника.
"""

from __future__ import annotations

import logging

from django.http import Http404
from django_ratelimit.exceptions import Ratelimited
from ninja import NinjaAPI
from ninja.errors import HttpError, ValidationError

from .errors import BusinessError, ErrorCode

logger = logging.getLogger(__name__)


def register_error_handlers(api: NinjaAPI) -> None:
    """Подключить все хендлеры к экземпляру NinjaAPI."""

    @api.exception_handler(BusinessError)
    def _handle_business_error(request, exc: BusinessError):
        return api.create_response(request, exc.to_payload(), status=exc.status)

    @api.exception_handler(ValidationError)
    def _handle_validation_error(request, exc: ValidationError):
        # Ninja упаковывает ошибки в exc.errors: list[{loc, msg, type}]
        fields: dict[str, list[str]] = {}
        for error in exc.errors:
            loc = error.get("loc") or []
            # loc выглядит как ("body", "field_name"); берём последнее имя поля
            field_name = str(loc[-1]) if loc else "non_field_errors"
            fields.setdefault(field_name, []).append(error.get("msg", "Invalid value"))

        payload = {
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "Проверьте корректность заполнения формы",
                "fields": fields,
            }
        }
        return api.create_response(request, payload, status=422)

    @api.exception_handler(Http404)
    def _handle_http404(request, exc: Http404):
        payload = {
            "error": {
                "code": ErrorCode.NOT_FOUND,
                "message": "Запрашиваемый ресурс не найден",
            }
        }
        return api.create_response(request, payload, status=404)

    @api.exception_handler(Ratelimited)
    def _handle_ratelimited(request, exc: Ratelimited):
        payload = {
            "error": {
                "code": ErrorCode.RATE_LIMITED,
                "message": "Слишком много обращений. Попробуйте позже.",
            }
        }
        return api.create_response(request, payload, status=429)

    @api.exception_handler(HttpError)
    def _handle_http_error(request, exc: HttpError):
        # Ninja HttpError используется для ручных raise HttpError(status, msg)
        code = _http_status_to_code(exc.status_code)
        payload = {"error": {"code": code, "message": str(exc) or code}}
        return api.create_response(request, payload, status=exc.status_code)

    @api.exception_handler(Exception)
    def _handle_internal_error(request, exc: Exception):
        logger.exception("Unhandled exception in API: %s", exc)
        payload = {
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "Внутренняя ошибка сервера",
            }
        }
        return api.create_response(request, payload, status=500)


def _http_status_to_code(status_code: int) -> str:
    """Маппинг HTTP-кода в нашу строковую константу ErrorCode."""
    return {
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.UNAUTHORIZED,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.EMAIL_ALREADY_TAKEN,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMITED,
    }.get(status_code, ErrorCode.INTERNAL_ERROR)
