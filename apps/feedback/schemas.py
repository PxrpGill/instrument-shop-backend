"""Pydantic-схемы модуля feedback.

Контракт: contracts/feedback/submit.json — POST /api/feedback.

Валидация на бэке дублирует фронтовую (FULL_NAME_VALIDATION / PHONE_VALIDATION),
поскольку фронт может слать что угодно. При ошибке отдаём 422 с раскладкой по
полям (см. apps.shared.exception_handlers).
"""

from __future__ import annotations

import re

from ninja import Schema
from pydantic import ConfigDict, EmailStr, Field, field_validator


# Российский формат: +7 (XXX) XXX-XX-XX, разделители — пробелы/тире/опц. скобки.
_PHONE_RE = re.compile(
    r"^(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$"
)


class FeedbackSubmitRequest(Schema):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str
    message: str = Field(..., min_length=1, max_length=2000)
    agreement: bool

    @field_validator("full_name")
    @classmethod
    def _validate_full_name(cls, value: str) -> str:
        value = value.strip()
        if any(ch.isdigit() for ch in value):
            raise ValueError("Имя не должно содержать цифр")
        if "  " in value:
            raise ValueError("Имя не должно содержать двойных пробелов")
        if len(value) < 2:
            raise ValueError("Имя должно содержать минимум 2 символа")
        return value

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not _PHONE_RE.match(value):
            raise ValueError(
                "Введите корректный номер телефона в формате +7 (XXX) XXX-XX-XX"
            )
        return value

    @field_validator("agreement")
    @classmethod
    def _validate_agreement(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Необходимо согласие с обработкой персональных данных")
        return value


class FeedbackSubmitResponse(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": 88,
        "message": "Спасибо! Ваше обращение принято. Мы свяжемся с вами в ближайшее время.",
    }})

    id: int
    message: str
