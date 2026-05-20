"""Бизнес-логика модуля feedback."""

from __future__ import annotations

from typing import Optional

from django.http import HttpRequest

from .models import FeedbackMessage

SUCCESS_MESSAGE = (
    "Ваше обращение принято. Мы свяжемся с вами в течение рабочего дня."
)


def _client_ip(request: Optional[HttpRequest]) -> Optional[str]:
    """Достать IP клиента; учитывает X-Forwarded-For за reverse-прокси."""
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


def create_feedback(
    *,
    full_name: str,
    email: str,
    phone: str,
    message: str,
    request: Optional[HttpRequest] = None,
) -> FeedbackMessage:
    return FeedbackMessage.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        message=message,
        ip_address=_client_ip(request),
    )
