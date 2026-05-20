"""Санитайзинг HTML, поступающего из админки.

Все поля, которые пользователь редактирует в TinyMCE/CKEditor и которые
фронт затем рендерит через dangerouslySetInnerHTML (page content, news
description, product descriptionParameters и т.п.), обязаны пройти
через sanitize_html на save, иначе XSS.
"""

from __future__ import annotations

import bleach

ALLOWED_TAGS = [
    "h2",
    "h3",
    "h4",
    "p",
    "br",
    "strong",
    "em",
    "u",
    "s",
    "blockquote",
    "ul",
    "ol",
    "li",
    "a",
    "span",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "span": ["class"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto", "tel"]


def sanitize_html(text: str | None) -> str:
    """Очистить HTML от опасных тегов/атрибутов.

    Сохраняет основные форматирующие теги + ссылки. Все script, iframe,
    style, on*-обработчики событий и javascript:-протоколы вырезаются.
    Пустая строка/None возвращаются как пустая строка.
    """
    if not text:
        return ""

    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
