"""Эндпоинты модуля «Избранное».

Контракты:
- GET /api/favorites           → contracts/favorites/list.json
- POST /api/favorites/{id}     → contracts/favorites/toggle.json
- DELETE /api/favorites/{id}   → contracts/favorites/toggle.json
"""

from __future__ import annotations

from django.http import HttpRequest
from ninja import Router

from apps.users.api.ninja_auth import customer_auth
from apps.users.models import Customer

from .schemas import FavoriteToggleResponse, FavoritesListResponse
from .services import add_favorite, list_favorites, remove_favorite

router = Router(tags=["Favorites"])


@router.get(
    "",
    auth=customer_auth,
    response=FavoritesListResponse,
    summary="Список избранного",
)
def get_favorites(request: HttpRequest):
    customer: Customer = request.auth
    return list_favorites(customer, request)


@router.post(
    "/{product_id}",
    auth=customer_auth,
    response={200: FavoriteToggleResponse},
    summary="Добавить товар в избранное",
)
def post_favorite(request: HttpRequest, product_id: int):
    customer: Customer = request.auth
    return 200, add_favorite(customer, product_id)


@router.delete(
    "/{product_id}",
    auth=customer_auth,
    response={204: None},
    summary="Удалить товар из избранного",
)
def delete_favorite(request: HttpRequest, product_id: int):
    customer: Customer = request.auth
    remove_favorite(customer, product_id)
    return 204, None
