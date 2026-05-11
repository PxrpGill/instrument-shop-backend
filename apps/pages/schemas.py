"""
Pydantic schemas for pages API.
"""

from typing import Optional

from ninja import Schema


class ContentBlockOut(Schema):
    """Схема для отображения контентного блока через API."""

    id: int
    block_type: str
    content: dict


class PageOut(Schema):
    """Схема для отображения страницы через API."""

    id: int
    title: str
    slug: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image: Optional[str] = None
    blocks: list[ContentBlockOut]
