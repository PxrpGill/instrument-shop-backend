"""JWT-хелперы для внутренних эндпоинтов (orders, products, role admin).

Новый публичный auth по контракту /api/auth/* использует Ninja-механизм
HttpBearer (см. `ninja_auth.py`). Эта функция нужна другим роутерам,
которые ещё не переведены на этот механизм. Когда они будут переписаны
под `auth=customer_auth`, файл можно удалить.
"""

from __future__ import annotations

from django.http import HttpRequest
from ninja.errors import HttpError
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.users.models import Customer


def get_customer_from_request(request: HttpRequest) -> Customer:
    """Резолвить Customer из Authorization: Bearer заголовка."""
    auth_header = ""
    for key in request.META:
        if key.upper() == "HTTP_AUTHORIZATION":
            auth_header = request.META[key]
            break

    if not auth_header:
        raise HttpError(status_code=401, message="Требуется авторизация")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HttpError(status_code=401, message="Неверный формат токена")

    token_str = parts[1]

    try:
        token = AccessToken(token_str)
        customer_id = token.get("customer_id")

        if not customer_id:
            raise HttpError(status_code=401, message="Невалидный токен")

        return Customer.objects.prefetch_related("roles").get(
            id=customer_id, is_active=True
        )
    except (InvalidToken, TokenError, Customer.DoesNotExist):
        raise HttpError(status_code=401, message="Невалидный токен")
