"""
Public API endpoints for pages.
No authentication required — pages are public content.
"""

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from apps.pages.models import BlockStatusChoices, Page
from apps.pages.schemas import ContentBlockOut, PageOut

# =============================================================================
# Router
# =============================================================================
router = Router(tags=["Pages"])


@router.get(
    "/pages/{slug}/",
    response=PageOut,
    description="Получить страницу по slug с опубликованными блоками",
    summary="Get page with published blocks",
)
def get_page(request: HttpRequest, slug: str):
    """Get a page by slug with its published blocks in order.

    Returns only blocks with status PUBLISHED,
    ordered by their position on the page.
    """
    page = get_object_or_404(
        Page.objects.prefetch_related("page_blocks__block"),
        slug=slug,
    )

    # Get published blocks in correct order
    published_page_blocks = (
        page.page_blocks.filter(block__status=BlockStatusChoices.PUBLISHED)
        .order_by("order")
        .select_related("block")
    )

    return PageOut(
        id=page.id,
        title=page.title,
        slug=page.slug,
        meta_title=page.meta_title or None,
        meta_description=page.meta_description or None,
        og_image=page.og_image.url if page.og_image else None,
        blocks=[
            ContentBlockOut(
                id=pb.block.id,
                block_type=pb.block.block_type,
                content=pb.block.content,
            )
            for pb in published_page_blocks
        ],
    )
