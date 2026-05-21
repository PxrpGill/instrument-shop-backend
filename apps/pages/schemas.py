"""Pydantic-схемы публичных страниц.

Соответствуют контрактам `contracts/pages/*.json`. Все опциональные секции
помечены как `Optional` — сериализатор не возвращает их в JSON, если
редактор не заполнил данные (правило README §«Правила работы для AI-агента»).
"""

from typing import List, Optional

from ninja import Schema
from pydantic import ConfigDict

from apps.shared.schemas import PictureSchema, SiteLink


# =============================================================================
# Home page
# =============================================================================


class HomeHero(Schema):
    title: str
    description: str
    button: SiteLink
    poster: Optional[PictureSchema] = None


class HomeAbout(Schema):
    title: str
    content: str
    poster: Optional[PictureSchema] = None


class HomeReviewAuthor(Schema):
    fullName: str
    icon: Optional[str] = None


class HomeReviewItem(Schema):
    title: str
    description: str
    grade: int
    author: HomeReviewAuthor


class HomeReviews(Schema):
    title: str
    reviews: List[HomeReviewItem]


class HomeShowcaseProduct(Schema):
    # Совпадает с shared/product (listing) — но мы возвращаем dict без жёсткой
    # типизации тут, чтобы переиспользовать serialize_product_list_item.
    pass


class HomeShowcaseGroup(Schema):
    title: str
    products: list


class HomeShowcase(Schema):
    title: str
    button: SiteLink
    showcases: List[HomeShowcaseGroup]


class HomeNewsCTA(Schema):
    title: str
    description: str
    button: SiteLink
    poster: Optional[PictureSchema] = None


class HomePageOut(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "hero": {
            "title": "Профессиональные инструменты с доставкой",
            "description": "Широкий выбор строительных инструментов от ведущих мировых производителей",
            "button": {"title": "Перейти в каталог", "href": "/catalog"},
            "poster": {"original": {"src": "/media/pages/hero-bg.jpg", "mobile": None}, "webp": None, "avif": None},
        },
        "about_company": {
            "title": "О компании",
            "content": "<p>Мы поставляем инструменты с 2010 года...</p>",
            "poster": None,
        },
        "reviews": {
            "title": "Отзывы покупателей",
            "reviews": [
                {
                    "title": "Отличный инструмент!",
                    "description": "Купил перфоратор, очень доволен качеством.",
                    "grade": 5,
                    "author": {"fullName": "Алексей Смирнов", "icon": None},
                }
            ],
        },
        "showcase": None,
        "news_cta": None,
    }})
    hero: Optional[HomeHero] = None
    about_company: Optional[HomeAbout] = None
    reviews: Optional[HomeReviews] = None
    showcase: Optional[HomeShowcase] = None
    news_cta: Optional[HomeNewsCTA] = None


# =============================================================================
# About-us / Buyers
# =============================================================================


class BannerWithoutButton(Schema):
    title: str
    description: str
    poster: Optional[PictureSchema] = None


class BannerPageOut(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "banner": {
            "title": "О компании",
            "description": "Интернет-магазин профессионального инструмента с 2010 года",
            "poster": {"original": {"src": "/media/pages/about-banner.jpg", "mobile": None}, "webp": None, "avif": None},
        },
        "content": "<p>Мы специализируемся на продаже профессионального инструмента...</p>",
    }})
    banner: Optional[BannerWithoutButton] = None
    content: Optional[str] = None


# =============================================================================
# Feedback
# =============================================================================


class FeedbackSection(Schema):
    title: str
    description: str


class FeedbackPageOut(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "section": {
            "title": "Обратная связь",
            "description": "Оставьте заявку и мы свяжемся с вами в течение рабочего дня",
        },
        "news_cta": {
            "title": "Читайте наш блог",
            "description": "Обзоры, советы и новости мира инструментов",
            "button": {"title": "Перейти в новости", "href": "/news"},
            "poster": None,
        },
    }})
    section: Optional[FeedbackSection] = None
    news_cta: Optional[HomeNewsCTA] = None


# =============================================================================
# Legal documents
# =============================================================================


class LegalSectionOut(Schema):
    id: str
    title: str
    content: str


class LegalDocumentOut(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "title": "Политика конфиденциальности",
        "last_updated": "2024-09-01",
        "sections": [
            {
                "id": "general",
                "title": "1. Общие положения",
                "content": "<p>Настоящая политика определяет порядок обработки персональных данных...</p>",
            },
            {
                "id": "data-collection",
                "title": "2. Сбор данных",
                "content": "<p>Мы собираем данные, которые вы предоставляете при регистрации...</p>",
            },
        ],
    }})
    title: str
    last_updated: str
    sections: List[LegalSectionOut]
