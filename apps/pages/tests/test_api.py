"""
Tests for pages API endpoints.
"""

import pytest
from ninja.testing import TestClient

from apps.pages.models import (
    BlockStatusChoices,
    BlockTypeChoices,
    ContentBlock,
    Page,
    PageBlock,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    """Create a TestClient for the pages router."""
    from instrument_shop.api import api

    return TestClient(api)


@pytest.fixture
def page_with_blocks():
    """Create a page with published and draft blocks."""
    page = Page.objects.create(title="Home", slug="home")

    hero_block = ContentBlock.objects.create(
        title="Hero Block",
        block_type=BlockTypeChoices.HERO,
        content={"title": "Welcome!", "subtitle": "Best instruments"},
        status=BlockStatusChoices.PUBLISHED,
    )
    faq_block = ContentBlock.objects.create(
        title="FAQ Block",
        block_type=BlockTypeChoices.FAQ,
        content={"items": [{"question": "Q1?", "answer": "A1!"}]},
        status=BlockStatusChoices.PUBLISHED,
    )
    draft_block = ContentBlock.objects.create(
        title="Draft Block",
        block_type=BlockTypeChoices.TEXT,
        content={"content": "Not ready yet"},
        status=BlockStatusChoices.DRAFT,
    )

    PageBlock.objects.create(page=page, block=hero_block, order=0)
    PageBlock.objects.create(page=page, block=faq_block, order=1)
    PageBlock.objects.create(page=page, block=draft_block, order=2)

    return page


@pytest.fixture
def page_with_meta():
    """Create a page with SEO metadata."""
    page = Page.objects.create(
        title="About",
        slug="about",
        meta_title="About Us - Instrument Shop",
        meta_description="Learn more about our company",
    )
    block = ContentBlock.objects.create(
        title="About Text",
        block_type=BlockTypeChoices.TEXT,
        content={"content": "<p>About us</p>"},
        status=BlockStatusChoices.PUBLISHED,
    )
    PageBlock.objects.create(page=page, block=block, order=0)
    return page


class TestGetPageEndpoint:
    """Test GET /v1/public/pages/{slug}/ endpoint."""

    def test_get_page_by_slug_success(self, api_client, page_with_blocks):
        """Should return page with published blocks."""
        response = api_client.get("/v1/public/pages/home/")

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Home"
        assert data["slug"] == "home"

    def test_only_published_blocks_returned(self, api_client, page_with_blocks):
        """Draft blocks should not appear in response."""
        response = api_client.get("/v1/public/pages/home/")
        data = response.json()

        assert len(data["blocks"]) == 2
        block_types = {b["block_type"] for b in data["blocks"]}
        assert "hero" in block_types
        assert "faq" in block_types
        assert "text" not in block_types

    def test_blocks_in_correct_order(self, api_client, page_with_blocks):
        """Blocks should be ordered by the 'order' field."""
        response = api_client.get("/v1/public/pages/home/")
        data = response.json()

        assert len(data["blocks"]) == 2
        assert data["blocks"][0]["block_type"] == "hero"
        assert data["blocks"][1]["block_type"] == "faq"

    def test_block_content_returned(self, api_client, page_with_blocks):
        """Block content should be included in response."""
        response = api_client.get("/v1/public/pages/home/")
        data = response.json()

        hero_block = data["blocks"][0]
        assert hero_block["block_type"] == "hero"
        assert hero_block["content"]["title"] == "Welcome!"
        assert hero_block["content"]["subtitle"] == "Best instruments"

    def test_block_ids_returned(self, api_client, page_with_blocks):
        """Block IDs should be in response."""
        response = api_client.get("/v1/public/pages/home/")
        data = response.json()

        for block in data["blocks"]:
            assert "id" in block
            assert isinstance(block["id"], int)

    def test_404_for_nonexistent_page(self, api_client):
        """Should return 404 for unknown slug."""
        response = api_client.get("/v1/public/pages/nonexistent/")
        assert response.status_code == 404

    def test_404_for_deleted_page(self, api_client, page_with_blocks):
        """Should return 404 after page deletion."""
        page_with_blocks.delete()
        response = api_client.get("/v1/public/pages/home/")
        assert response.status_code == 404

    def test_page_with_no_blocks(self, api_client):
        """Page with no blocks should return empty list."""
        page = Page.objects.create(title="Empty", slug="empty")
        _ = page  # avoid unused var
        response = api_client.get("/v1/public/pages/empty/")
        assert response.status_code == 200
        data = response.json()
        assert data["blocks"] == []

    def test_page_with_all_draft_blocks(self, api_client):
        """Page where all blocks are drafts should have empty blocks."""
        page = Page.objects.create(title="Draft Only", slug="draft-only")
        block = ContentBlock.objects.create(
            title="Draft",
            block_type=BlockTypeChoices.TEXT,
            status=BlockStatusChoices.DRAFT,
        )
        PageBlock.objects.create(page=page, block=block, order=0)

        response = api_client.get("/v1/public/pages/draft-only/")
        assert response.status_code == 200
        data = response.json()
        assert data["blocks"] == []


class TestPageMetaEndpoint:
    """Test SEO metadata in API response."""

    def test_meta_title_returned(self, api_client, page_with_meta):
        """Meta title should be in response."""
        response = api_client.get("/v1/public/pages/about/")
        data = response.json()
        assert data["meta_title"] == "About Us - Instrument Shop"

    def test_meta_description_returned(self, api_client, page_with_meta):
        """Meta description should be in response."""
        response = api_client.get("/v1/public/pages/about/")
        data = response.json()
        assert data["meta_description"] == "Learn more about our company"

    def test_meta_null_when_empty(self, api_client, page_with_blocks):
        """Empty meta fields should be null, not empty string."""
        response = api_client.get("/v1/public/pages/home/")
        data = response.json()
        assert data["meta_title"] is None
        assert data["meta_description"] is None

    def test_og_image_null_when_not_set(self, api_client, page_with_blocks):
        """OG image should be null when not uploaded."""
        response = api_client.get("/v1/public/pages/home/")
        data = response.json()
        assert data["og_image"] is None


class TestPageSchema:
    """Test API response structure."""

    def test_response_structure(self, api_client, page_with_blocks):
        """Response should have correct fields."""
        response = api_client.get("/v1/public/pages/home/")
        data = response.json()

        assert "id" in data
        assert "title" in data
        assert "slug" in data
        assert "meta_title" in data
        assert "meta_description" in data
        assert "og_image" in data
        assert "blocks" in data

    def test_block_structure(self, api_client, page_with_blocks):
        """Each block should have correct fields."""
        response = api_client.get("/v1/public/pages/home/")
        data = response.json()

        for block in data["blocks"]:
            assert "id" in block
            assert "block_type" in block
            assert "content" in block
