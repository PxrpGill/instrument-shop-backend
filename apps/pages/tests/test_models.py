"""
Tests for pages app models.
"""

import pytest
from django.db import IntegrityError

from apps.pages.models import (
    BlockStatusChoices,
    BlockTypeChoices,
    ContentBlock,
    Page,
    PageBlock,
)


class TestBlockStatusChoices:
    """Test block status choices."""

    def test_draft_status(self):
        assert BlockStatusChoices.DRAFT == "draft"
        assert BlockStatusChoices.DRAFT.label == "Черновик"

    def test_published_status(self):
        assert BlockStatusChoices.PUBLISHED == "published"
        assert BlockStatusChoices.PUBLISHED.label == "Опубликован"


class TestBlockTypeChoices:
    """Test block type choices."""

    def test_all_types_present(self):
        types = [choice.value for choice in BlockTypeChoices]
        expected = [
            "hero",
            "text",
            "faq",
            "features",
            "gallery",
            "reviews",
            "banner",
            "video",
            "statistics",
            "contacts",
        ]
        assert types == expected


class TestContentBlockModel:
    """Test ContentBlock model."""

    def test_create_content_block(self, db):
        block = ContentBlock.objects.create(
            title="Test Hero Block",
            block_type=BlockTypeChoices.HERO,
            content={"title": "Welcome", "subtitle": "To our shop"},
            status=BlockStatusChoices.PUBLISHED,
        )
        assert block.title == "Test Hero Block"
        assert block.block_type == "hero"
        assert block.content == {"title": "Welcome", "subtitle": "To our shop"}
        assert block.status == "published"

    def test_default_status_is_draft(self, db):
        block = ContentBlock.objects.create(
            title="Draft Block",
            block_type=BlockTypeChoices.TEXT,
        )
        assert block.status == BlockStatusChoices.DRAFT

    def test_default_content_is_empty_dict(self, db):
        block = ContentBlock.objects.create(
            title="Empty Content",
            block_type=BlockTypeChoices.TEXT,
        )
        assert block.content == {}

    def test_str_representation(self, db):
        block = ContentBlock.objects.create(
            title="FAQ Block",
            block_type=BlockTypeChoices.FAQ,
        )
        expected = "FAQ (вопросы-ответы): FAQ Block"
        assert str(block) == expected

    def test_ordering(self, db):
        block1 = ContentBlock.objects.create(
            title="Block A",
            block_type=BlockTypeChoices.TEXT,
        )
        block2 = ContentBlock.objects.create(
            title="Block B",
            block_type=BlockTypeChoices.TEXT,
        )
        # Default ordering is -created_at (newest first)
        blocks = ContentBlock.objects.all()
        assert blocks[0] == block2
        assert blocks[1] == block1


class TestPageModel:
    """Test Page model."""

    def test_create_page(self, db):
        page = Page.objects.create(
            title="Main Page",
            slug="main",
            meta_title="Main Page SEO",
            meta_description="Description for main page",
        )
        assert page.title == "Main Page"
        assert page.slug == "main"
        assert page.meta_title == "Main Page SEO"
        assert page.meta_description == "Description for main page"

    def test_slug_auto_generation(self, db):
        page = Page.objects.create(title="About Us")
        assert page.slug == "about-us"

    def test_unique_slug(self, db):
        Page.objects.create(title="Page One", slug="my-page")
        with pytest.raises(IntegrityError):
            Page.objects.create(title="Page Two", slug="my-page")

    def test_str_representation(self, db):
        page = Page.objects.create(title="Contact Us", slug="contact")
        assert str(page) == "Contact Us"

    def test_ordering(self, db):
        page_b = Page.objects.create(title="Beta", slug="beta")
        page_a = Page.objects.create(title="Alpha", slug="alpha")
        pages = Page.objects.all()
        assert pages[0] == page_a
        assert pages[1] == page_b

    def test_page_with_blocks(self, db):
        page = Page.objects.create(title="Home", slug="home")
        block = ContentBlock.objects.create(
            title="Hero",
            block_type=BlockTypeChoices.HERO,
        )
        PageBlock.objects.create(page=page, block=block, order=0)

        assert page.blocks.count() == 1
        assert page.blocks.first() == block

    def test_meta_fields_blank_by_default(self, db):
        page = Page.objects.create(title="Simple Page", slug="simple")
        assert page.meta_title == ""
        assert page.meta_description == ""


class TestPageBlockModel:
    """Test PageBlock through model."""

    def test_create_page_block(self, db):
        page = Page.objects.create(title="Home", slug="home")
        block = ContentBlock.objects.create(
            title="Hero",
            block_type=BlockTypeChoices.HERO,
        )
        page_block = PageBlock.objects.create(page=page, block=block, order=1)

        assert page_block.page == page
        assert page_block.block == block
        assert page_block.order == 1

    def test_unique_together_constraint(self, db):
        page = Page.objects.create(title="Home", slug="home")
        block = ContentBlock.objects.create(
            title="Hero",
            block_type=BlockTypeChoices.HERO,
        )
        PageBlock.objects.create(page=page, block=block, order=0)

        with pytest.raises(IntegrityError):
            PageBlock.objects.create(page=page, block=block, order=1)

    def test_ordering_by_order_field(self, db):
        page = Page.objects.create(title="Home", slug="home")
        block_a = ContentBlock.objects.create(
            title="Block A",
            block_type=BlockTypeChoices.TEXT,
        )
        block_b = ContentBlock.objects.create(
            title="Block B",
            block_type=BlockTypeChoices.TEXT,
        )
        PageBlock.objects.create(page=page, block=block_a, order=1)
        PageBlock.objects.create(page=page, block=block_b, order=0)

        page_blocks = PageBlock.objects.all()
        assert page_blocks[0].block == block_b
        assert page_blocks[1].block == block_a

    def test_str_representation(self, db):
        page = Page.objects.create(title="Home", slug="home")
        block = ContentBlock.objects.create(
            title="Hero",
            block_type=BlockTypeChoices.HERO,
        )
        page_block = PageBlock.objects.create(page=page, block=block, order=0)
        expected = "Home → Hero (порядок: 0)"
        assert str(page_block) == expected


class TestPageBlockRelation:
    """Test page-block relationships."""

    def test_block_reusable_across_pages(self, db):
        """A block can be used on multiple pages."""
        block = ContentBlock.objects.create(
            title="Reusable FAQ",
            block_type=BlockTypeChoices.FAQ,
        )
        page1 = Page.objects.create(title="Home", slug="home")
        page2 = Page.objects.create(title="About", slug="about")

        PageBlock.objects.create(page=page1, block=block, order=0)
        PageBlock.objects.create(page=page2, block=block, order=0)

        assert page1.blocks.count() == 1
        assert page2.blocks.count() == 1
        assert block.pages.count() == 2

    def test_cascade_delete_page(self, db):
        """Deleting a page removes PageBlock but not ContentBlock."""
        block = ContentBlock.objects.create(
            title="Hero",
            block_type=BlockTypeChoices.HERO,
        )
        page = Page.objects.create(title="Home", slug="home")
        PageBlock.objects.create(page=page, block=block, order=0)

        page.delete()

        assert ContentBlock.objects.filter(id=block.id).exists()
        assert PageBlock.objects.count() == 0

    def test_cascade_delete_block(self, db):
        """Deleting a block removes PageBlock but not Page."""
        block = ContentBlock.objects.create(
            title="Hero",
            block_type=BlockTypeChoices.HERO,
        )
        page = Page.objects.create(title="Home", slug="home")
        PageBlock.objects.create(page=page, block=block, order=0)

        block.delete()

        assert Page.objects.filter(id=page.id).exists()
        assert PageBlock.objects.count() == 0
