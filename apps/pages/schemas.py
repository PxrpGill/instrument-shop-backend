"""Pydantic-схемы публичных страниц.

Соответствуют контрактам `contracts/pages/*.json`. Все опциональные секции
помечены как `Optional` — сериализатор не возвращает их в JSON, если
редактор не заполнил данные (правило README §«Правила работы для AI-агента»).
"""

from typing import List, Optional

from ninja import Schema

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
    banner: Optional[BannerWithoutButton] = None
    content: Optional[str] = None


# =============================================================================
# Feedback
# =============================================================================


class FeedbackSection(Schema):
    title: str
    description: str


class FeedbackPageOut(Schema):
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
    title: str
    last_updated: str
    sections: List[LegalSectionOut]
