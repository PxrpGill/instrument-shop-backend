"""Сериализаторы Page → dict по контрактам `contracts/pages/*`.

Возвращаем чистые dict (а не Pydantic-экземпляры): фронт ожидает, что
опциональные секции/поля **отсутствуют** в JSON, а не выставлены в `null`.
Поэтому ключи добавляются условно.
"""

from __future__ import annotations

from typing import Optional

from django.http import HttpRequest

from apps.products.catalog_serializers import serialize_product_list_item
from apps.shared.services.picture import image_to_picture

from .models import (
    AboutUsPage,
    BuyersPage,
    FeedbackPage,
    HomePage,
    LegalDocument,
)


# =============================================================================
# Home
# =============================================================================


def serialize_home_page(page: HomePage, request: Optional[HttpRequest] = None) -> dict:
    out: dict = {}

    hero = _hero_section(page, request)
    if hero is not None:
        out["hero"] = hero

    about = _about_section(page, request)
    if about is not None:
        out["about_company"] = about

    reviews = _reviews_section(page, request)
    if reviews is not None:
        out["reviews"] = reviews

    showcase = _showcase_section(page, request)
    if showcase is not None:
        out["showcase"] = showcase

    news_cta = _news_cta_section(
        title=page.news_cta_title,
        description=page.news_cta_description,
        button_title=page.news_cta_button_title,
        button_href=page.news_cta_button_href,
        poster=page.news_cta_poster,
        request=request,
    )
    if news_cta is not None:
        out["news_cta"] = news_cta

    return out


def _hero_section(page: HomePage, request: Optional[HttpRequest]) -> Optional[dict]:
    if not page.hero_title:
        return None
    section: dict = {
        "title": page.hero_title,
        "description": page.hero_description or "",
        "button": {
            "title": page.hero_button_title or "",
            "href": page.hero_button_href or "",
        },
    }
    poster = image_to_picture(page.hero_poster, request)
    if poster is not None:
        section["poster"] = poster
    return section


def _about_section(page: HomePage, request: Optional[HttpRequest]) -> Optional[dict]:
    if not page.about_title:
        return None
    section: dict = {
        "title": page.about_title,
        "content": page.about_content or "",
    }
    poster = image_to_picture(page.about_poster, request)
    if poster is not None:
        section["poster"] = poster
    return section


def _reviews_section(page: HomePage, request: Optional[HttpRequest]) -> Optional[dict]:
    if not page.reviews_title:
        return None
    items: list[dict] = []
    home_reviews = (
        page.home_reviews.select_related("review", "review__author_icon")
        .filter(review__is_published=True)
        .order_by("order")
    )
    for link in home_reviews:
        review = link.review
        author: dict = {"fullName": review.author_full_name}
        icon_picture = image_to_picture(review.author_icon, request)
        if icon_picture is not None:
            # По контракту icon — строка URL, не picture. Берём src оригинала
            # либо webp, либо первый доступный.
            icon_url = (
                (icon_picture.get("original") or {}).get("src")
                or (icon_picture.get("webp") or {}).get("src")
                or (icon_picture.get("avif") or {}).get("src")
            )
            if icon_url:
                author["icon"] = icon_url
        items.append(
            {
                "title": review.title,
                "description": review.description,
                "grade": review.grade,
                "author": author,
            }
        )
    return {"title": page.reviews_title, "reviews": items}


def _showcase_section(page: HomePage, request: Optional[HttpRequest]) -> Optional[dict]:
    if not page.showcase_title:
        return None
    groups: list[dict] = []
    showcases = page.showcases.order_by("order").prefetch_related(
        "showcase_products__product__images__image",
        "showcase_products__product__categories",
    )
    for showcase in showcases:
        products: list[dict] = []
        for link in showcase.showcase_products.order_by("order"):
            products.append(serialize_product_list_item(link.product, request))
        groups.append({"title": showcase.title, "products": products})

    return {
        "title": page.showcase_title,
        "button": {
            "title": page.showcase_button_title or "",
            "href": page.showcase_button_href or "",
        },
        "showcases": groups,
    }


def _news_cta_section(
    *,
    title: str,
    description: str,
    button_title: str,
    button_href: str,
    poster,
    request: Optional[HttpRequest],
) -> Optional[dict]:
    if not title:
        return None
    section: dict = {
        "title": title,
        "description": description or "",
        "button": {"title": button_title or "", "href": button_href or ""},
    }
    poster_dict = image_to_picture(poster, request)
    if poster_dict is not None:
        section["poster"] = poster_dict
    return section


# =============================================================================
# About-us / Buyers (banner + content)
# =============================================================================


def serialize_banner_page(
    page: AboutUsPage | BuyersPage, request: Optional[HttpRequest] = None
) -> dict:
    out: dict = {}
    banner = _banner_section(page, request)
    if banner is not None:
        out["banner"] = banner
    if page.content:
        out["content"] = page.content
    return out


def _banner_section(page, request: Optional[HttpRequest]) -> Optional[dict]:
    if not page.banner_title:
        return None
    section: dict = {
        "title": page.banner_title,
        "description": page.banner_description or "",
    }
    poster = image_to_picture(page.banner_poster, request)
    if poster is not None:
        section["poster"] = poster
    return section


# =============================================================================
# Feedback
# =============================================================================


def serialize_feedback_page(
    page: FeedbackPage, request: Optional[HttpRequest] = None
) -> dict:
    out: dict = {}
    if page.section_title:
        out["section"] = {
            "title": page.section_title,
            "description": page.section_description or "",
        }
    news_cta = _news_cta_section(
        title=page.news_cta_title,
        description=page.news_cta_description,
        button_title=page.news_cta_button_title,
        button_href=page.news_cta_button_href,
        poster=page.news_cta_poster,
        request=request,
    )
    if news_cta is not None:
        out["news_cta"] = news_cta
    return out


# =============================================================================
# Legal documents
# =============================================================================


def serialize_legal_document(doc: LegalDocument) -> dict:
    return {
        "title": doc.title,
        "last_updated": doc.last_updated,
        "sections": [
            {"id": s.anchor_id, "title": s.title, "content": s.content}
            for s in doc.sections.order_by("order")
        ],
    }
