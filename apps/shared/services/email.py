"""Утилиты отправки email.

В dev используется console backend (Django пишет письма в stdout контейнера),
в prod — SMTP, настройки через переменные окружения EMAIL_HOST и т.д.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_url: str) -> None:
    """Отправить письмо со ссылкой для сброса пароля.

    Не возвращает ошибку наружу: forgot-password должен всегда отвечать 200
    (защита от энумерации). Любые проблемы с отправкой логируем.
    """
    subject = "Сброс пароля в Instrument Shop"
    message = (
        "Здравствуйте!\n\n"
        "Вы (или кто-то другой) запросили сброс пароля.\n"
        f"Перейдите по ссылке, чтобы задать новый пароль:\n\n{reset_url}\n\n"
        "Если вы не запрашивали сброс — просто проигнорируйте это письмо. "
        "Ссылка действительна 30 минут.\n"
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@instrument-shop.local")

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Не удалось отправить письмо сброса пароля на %s", to_email)
