"""Сервис восстановления пароля.

Поток:
1. Клиент вызывает POST /api/auth/forgot-password с email.
   Сервер всегда отвечает 200 (защита от энумерации). Если customer существует,
   создаётся PasswordResetToken и отправляется письмо со ссылкой.
2. Клиент переходит по ссылке, вводит новый пароль, фронт вызывает
   POST /api/auth/reset-password с {token, password}.
   Сервер валидирует токен, меняет пароль, помечает токен использованным.

После успешного сброса все активные refresh-токены пользователя должны быть
отозваны — это сделано на уровне controller через blacklist.
"""

from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from django.contrib.auth.hashers import make_password

from apps.shared.errors import invalid_token
from apps.shared.services.email import send_password_reset_email
from apps.users.models import Customer, PasswordResetToken
from apps.users.services.customer_service import CustomerService

logger = logging.getLogger(__name__)


def request_reset(email: str) -> None:
    """Запросить сброс пароля.

    Если customer существует — генерируется одноразовый токен и отправляется
    email со ссылкой. Если нет — операция тихо пропускается (контроллер
    в любом случае отдаст 200).
    """
    customer = CustomerService.get_customer_by_email(email)
    if customer is None or not customer.is_active:
        logger.info("forgot-password: email %s не найден или неактивен", email)
        return

    token = PasswordResetToken.issue_for(customer)
    reset_url = _build_reset_url(token.token)
    send_password_reset_email(customer.email, reset_url)


def consume_reset(token_value: str, new_password: str) -> Customer:
    """Применить токен и сменить пароль.

    Бросает BusinessError(INVALID_TOKEN) если токен не существует, истёк
    или уже использован. Возвращает customer на случай, если контроллеру
    нужно дополнительно выполнить действия (например, blacklist'нуть его
    активные refresh-токены).
    """
    token: Optional[PasswordResetToken] = (
        PasswordResetToken.objects.select_related("customer")
        .filter(token=token_value)
        .first()
    )
    if token is None or not token.is_valid:
        raise invalid_token("Ссылка для сброса пароля недействительна или истекла")

    customer = token.customer
    customer.password_hash = make_password(new_password)
    customer.save(update_fields=["password_hash"])
    token.mark_used()
    return customer


def _build_reset_url(token: str) -> str:
    """Собрать URL для письма.

    Шаблон берётся из settings.PASSWORD_RESET_URL_TEMPLATE — там можно
    использовать `{token}` плейсхолдер. Например:
        https://shop.example.com/reset-password?token={token}
    """
    template = getattr(
        settings,
        "PASSWORD_RESET_URL_TEMPLATE",
        "http://localhost:3000/reset-password?token={token}",
    )
    return template.format(token=token)
