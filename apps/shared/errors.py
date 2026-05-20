"""Единый формат ошибок API по контракту shared/error.json.

Любая 4xx/5xx ошибка отдаётся фронту в виде:
    {"error": {"code": "CODE_IN_SCREAMING_SNAKE", "message": "...", "fields?": {...}}}

Хендлеры регистрируются в `instrument_shop/api.py::register_error_handlers`.
"""

from __future__ import annotations

from typing import Final, Optional


class ErrorCode:
    """Коды ошибок, согласованные с README контрактов и фронтом."""

    UNAUTHORIZED: Final[str] = "UNAUTHORIZED"
    INVALID_TOKEN: Final[str] = "INVALID_TOKEN"
    INVALID_CREDENTIALS: Final[str] = "INVALID_CREDENTIALS"
    NOT_FOUND: Final[str] = "NOT_FOUND"
    EMAIL_ALREADY_TAKEN: Final[str] = "EMAIL_ALREADY_TAKEN"
    VALIDATION_ERROR: Final[str] = "VALIDATION_ERROR"
    RATE_LIMITED: Final[str] = "RATE_LIMITED"
    INTERNAL_ERROR: Final[str] = "INTERNAL_ERROR"


class BusinessError(Exception):
    """Бизнес-ошибка с фиксированным HTTP-кодом и форматом ответа.

    Используется в сервисах и контроллерах для возврата ожидаемых ошибок
    (404 NOT_FOUND, 409 EMAIL_ALREADY_TAKEN и т.п.). Глобальный handler
    в api.py конвертирует её в JSON shared/error.
    """

    def __init__(
        self,
        code: str,
        message: str,
        status: int,
        fields: Optional[dict] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.fields = fields

    def to_payload(self) -> dict:
        error: dict = {"code": self.code, "message": self.message}
        if self.fields:
            error["fields"] = self.fields
        return {"error": error}


# Готовые конструкторы для частых случаев — сокращают boilerplate в сервисах.

def not_found(message: str = "Запрашиваемый ресурс не найден") -> BusinessError:
    return BusinessError(ErrorCode.NOT_FOUND, message, status=404)


def unauthorized(message: str = "Требуется авторизация") -> BusinessError:
    return BusinessError(ErrorCode.UNAUTHORIZED, message, status=401)


def invalid_credentials(message: str = "Неверный email или пароль") -> BusinessError:
    return BusinessError(ErrorCode.INVALID_CREDENTIALS, message, status=401)


def invalid_token(message: str = "Токен недействителен или истёк") -> BusinessError:
    return BusinessError(ErrorCode.INVALID_TOKEN, message, status=401)


def email_already_taken(
    message: str = "Пользователь с таким email уже зарегистрирован",
) -> BusinessError:
    return BusinessError(ErrorCode.EMAIL_ALREADY_TAKEN, message, status=409)


def validation_error(
    fields: dict,
    message: str = "Проверьте корректность заполнения формы",
) -> BusinessError:
    return BusinessError(
        ErrorCode.VALIDATION_ERROR, message, status=422, fields=fields
    )


def rate_limited(
    message: str = "Слишком много запросов. Попробуйте позже.",
) -> BusinessError:
    return BusinessError(ErrorCode.RATE_LIMITED, message, status=429)
