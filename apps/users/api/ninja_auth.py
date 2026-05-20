"""Ninja-аутентификация для Customer через JWT access-токен.

Использование в роутере:
    @router.post("/logout", auth=customer_auth)
    def logout(request, ...):
        customer = request.auth  # Ninja подставляет результат __call__

`request.auth` будет Customer или Ninja вернёт 401 автоматически (но
наш exception handler перехватит и отдаст shared/error формат).
"""

from __future__ import annotations

from typing import Optional

from ninja.security import HttpBearer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.shared.errors import unauthorized
from apps.users.models import Customer


class CustomerBearer(HttpBearer):
    """Bearer-аутентификация: проверяет access-токен и резолвит Customer."""

    def authenticate(self, request, token: str) -> Optional[Customer]:
        try:
            access = AccessToken(token)
        except (InvalidToken, TokenError):
            raise unauthorized()

        customer_id = access.get("customer_id")
        if not customer_id:
            raise unauthorized()

        customer = (
            Customer.objects.prefetch_related("roles")
            .filter(id=customer_id, is_active=True)
            .first()
        )
        if customer is None:
            raise unauthorized()

        return customer


customer_auth = CustomerBearer()
