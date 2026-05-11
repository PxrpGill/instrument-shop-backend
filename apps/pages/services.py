"""
Business logic for pages management.
"""

from typing import Optional

from django.db.models import Prefetch

from apps.pages.models import BlockStatusChoices, ContentBlock, Page


def get_page_by_slug(slug: str) -> Optional[Page]:
    """Get a page by slug with prefetched published blocks in order.

    Args:
        slug: URL-идентификатор страницы.

    Returns:
        Page instance or None if not found.
    """
    try:
        page = Page.objects.prefetch_related(
            Prefetch(
                "page_blocks",
                queryset=Page.objects.get(slug=slug)
                .page_blocks.select_related("block")
                .filter(block__status=BlockStatusChoices.PUBLISHED)
                .order_by("order"),
            )
        ).get(slug=slug)
        return page
    except Page.DoesNotExist:
        return None


def get_published_blocks_for_page(page: Page) -> list[ContentBlock]:
    """Get only published blocks for a page in correct order.

    Args:
        page: Page instance.

    Returns:
        List of published ContentBlock instances ordered by position.
    """
    page_blocks = (
        page.page_blocks.select_related("block")
        .filter(block__status=BlockStatusChoices.PUBLISHED)
        .order_by("order")
    )
    return [pb.block for pb in page_blocks]
