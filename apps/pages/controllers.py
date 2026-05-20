"""Публичные эндпоинты публичных страниц.

Все эндпоинты не требуют аутентификации. Возвращают чистые dict (не Pydantic),
поэтому опциональные поля просто отсутствуют в JSON, а не равны null.
"""

from __future__ import annotations

from django.http import HttpRequest
from ninja import Router

from apps.shared.errors import not_found

from .models import (
    AboutUsPage,
    BuyersPage,
    FeedbackPage,
    HomePage,
    LegalDocument,
)
from .services import (
    serialize_banner_page,
    serialize_feedback_page,
    serialize_home_page,
    serialize_legal_document,
)

router = Router(tags=["Pages"])


@router.get(
    "/home",
    description="Главная страница сайта (контракт contracts/pages/home.json).",
    summary="Get home page",
)
def get_home_page(request: HttpRequest):
    page = HomePage.get_solo()
    return serialize_home_page(page, request)


@router.get(
    "/about-us",
    description="Страница «О компании» (контракт contracts/pages/about-us.json).",
    summary="Get about-us page",
)
def get_about_us_page(request: HttpRequest):
    page = AboutUsPage.get_solo()
    return serialize_banner_page(page, request)


@router.get(
    "/buyers",
    description="Страница «Покупателям» (контракт contracts/pages/buyers.json).",
    summary="Get buyers page",
)
def get_buyers_page(request: HttpRequest):
    page = BuyersPage.get_solo()
    return serialize_banner_page(page, request)


@router.get(
    "/feedback",
    description="Страница обратной связи (контракт contracts/pages/feedback.json).",
    summary="Get feedback page",
)
def get_feedback_page(request: HttpRequest):
    page = FeedbackPage.get_solo()
    return serialize_feedback_page(page, request)


@router.get(
    "/legal/{slug}",
    description="Юридический документ по slug (privacy-policy, user-agreement, personal-data-consent).",
    summary="Get legal document",
)
def get_legal_document(request: HttpRequest, slug: str):
    try:
        doc = LegalDocument.objects.prefetch_related("sections").get(pk=slug)
    except LegalDocument.DoesNotExist as exc:
        raise not_found("Документ не найден") from exc
    return serialize_legal_document(doc)
