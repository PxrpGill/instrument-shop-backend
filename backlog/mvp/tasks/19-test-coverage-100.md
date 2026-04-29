# Task 19: Test Coverage 100%

## Objective
Achieve 100% test coverage for the `pages` app and ensure no regressions in existing tests.

## Subtasks
- BE-056: Achieve 100% coverage for models
- BE-057: Achieve 100% coverage for schemas
- BE-058: Achieve 100% coverage for services
- BE-059: Achieve 100% coverage for API endpoints
- BE-060: Achieve 100% coverage for admin
- BE-061: Run full test suite and verify no regressions

## Implementation Details

### 1. Coverage Analysis

Run coverage to identify untested code:
```bash
docker-compose exec web python -m pytest apps/pages/tests/ --cov=apps.pages --cov-report=term-missing
```

### 2. Complete Model Tests (`apps/pages/tests/test_models.py`)

Ensure 100% coverage:
```python
import pytest
from apps.pages.models import Page, ContentBlock

class TestPageModel:
    def test_create_page_minimal(self):
        """Test creating page with required fields only."""
        page = Page.objects.create(title="Test Page", slug="test-page")
        assert page.title == "Test Page"
        assert page.slug == "test-page"
        assert page.is_published is False
        assert page.meta_title == ""
        assert page.meta_description == ""

    def test_create_page_full(self):
        """Test creating page with all fields."""
        page = Page.objects.create(
            title="Full Page",
            slug="full-page",
            meta_title="SEO Title",
            meta_description="SEO Description",
            is_published=True,
        )
        assert page.meta_title == "SEO Title"
        assert page.is_published is True

    def test_slug_uniqueness(self):
        """Test that slugs must be unique."""
        Page.objects.create(title="Page 1", slug="same-slug")
        with pytest.raises(Exception):  # IntegrityError
            Page.objects.create(title="Page 2", slug="same-slug")

    def test_page_str(self):
        """Test string representation."""
        page = Page.objects.create(title="My Page", slug="my-page")
        assert str(page) == "My Page"

    def test_page_meta_verbose_name(self):
        """Test Russian verbose_name."""
        assert Page._meta.verbose_name == "Страница"
        assert Page._meta.verbose_name_plural == "Страницы"

    def test_page_ordering(self):
        """Test default ordering by -created_at."""
        assert Page._meta.ordering == ["-created_at"]

class TestContentBlockModel:
    def test_create_text_block(self, page):
        """Test creating a text block."""
        block = ContentBlock.objects.create(
            page=page,
            block_type="text",
            content={"text": "<p>Rich text content</p>"},
            order=0,
        )
        assert block.block_type == "text"
        assert block.content["text"] == "<p>Rich text content</p>"

    def test_create_image_block(self, page):
        """Test creating an image block."""
        block = ContentBlock.objects.create(
            page=page,
            block_type="image",
            content={"image_url": "/media/image.jpg", "alt_text": "Alt", "caption": "Caption"},
            order=1,
        )
        assert block.content["image_url"] == "/media/image.jpg"

    def test_create_hero_banner_block(self, page):
        """Test creating a hero banner block."""
        block = ContentBlock.objects.create(
            page=page,
            block_type="hero_banner",
            content={
                "title": "Hero Title",
                "subtitle": "Subtitle",
                "background_image": "/media/hero.jpg",
                "button_text": "Click",
                "button_url": "/click",
            },
            order=2,
        )
        assert block.content["title"] == "Hero Title"

    def test_create_cta_block(self, page):
        """Test creating a CTA block."""
        block = ContentBlock.objects.create(
            page=page,
            block_type="cta",
            content={
                "title": "CTA Title",
                "description": "Description",
                "button_text": "Action",
                "button_url": "/action",
                "style": "primary",
            },
            order=3,
        )
        assert block.content["style"] == "primary"

    def test_block_ordering(self, page):
        """Test blocks are ordered by order field."""
        block1 = ContentBlock.objects.create(page=page, block_type="text", content={}, order=2)
        block2 = ContentBlock.objects.create(page=page, block_type="text", content={}, order=0)
        block3 = ContentBlock.objects.create(page=page, block_type="text", content={}, order=1)
        blocks = list(ContentBlock.objects.filter(page=page))
        assert blocks[0] == block2
        assert blocks[1] == block3
        assert blocks[2] == block1

    def test_block_str(self, page):
        """Test string representation."""
        block = ContentBlock.objects.create(
            page=page, block_type="text", content={}, order=0
        )
        assert "My Page" in str(block)  # page.title

    def test_block_meta_verbose_name(self):
        """Test Russian verbose_name."""
        assert ContentBlock._meta.verbose_name == "Контентный блок"
        assert ContentBlock._meta.verbose_name_plural == "Контентные блоки"

    def test_block_type_choices(self):
        """Test block type choices have Russian translations."""
        choices = dict(ContentBlock.BlockType.choices)
        assert choices["text"] == "Текст"
        assert choices["image"] == "Изображение"
```

### 3. Complete Service Tests (`apps/pages/tests/test_services.py`)

Add missing coverage:
- Test error cases (page not found, block not found)
- Test cascade delete
- Test reorder with invalid block_ids
- Test edge cases (empty content, special characters)

### 4. Complete API Tests (`apps/pages/tests/test_api.py`)

Add missing coverage:
- Test 404 for non-existent page
- Test invalid JSON content
- Test invalid block_type
- Test reorder with duplicate block_ids
- Test slug conflicts on create/update
- Test meta fields validation

### 5. Admin Tests (`apps/pages/tests/test_admin.py`) (if needed for 100%)

```python
@pytest.mark.django_db
class TestPageAdmin:
    def test_page_admin_list(self, admin_client):
        """Test admin list view."""
        response = admin_client.get("/admin/pages/page/")
        assert response.status_code == 200

    def test_page_admin_create(self, admin_client):
        """Test creating page in admin."""
        response = admin_client.post("/admin/pages/page/add/", {
            "title": "Admin Page",
            "slug": "admin-page",
            "is_published": True,
        })
        assert response.status_code in [200, 302]  # Redirect on success
```

### 6. Coverage Commands

Check coverage per module:
```bash
# Models
docker-compose exec web python -m pytest apps/pages/tests/test_models.py --cov=apps.pages.models --cov-report=term-missing

# Schemas
docker-compose exec web python -m pytest apps/pages/tests/test_schemas.py --cov=apps.pages.schemas --cov-report=term-missing

# Services
docker-compose exec web python -m pytest apps/pages/tests/test_services.py --cov=apps.pages.services --cov-report=term-missing

# API
docker-compose exec web python -m pytest apps/pages/tests/test_api.py --cov=apps.pages.controllers --cov-report=term-missing

# Admin
docker-compose exec web python -m pytest apps/pages/tests/test_admin.py --cov=apps.pages.admin --cov-report=term-missing
```

### 7. Full Test Suite

Run all tests to ensure no regressions:
```bash
docker-compose exec web python -m pytest apps/ -v
```

Check total coverage:
```bash
docker-compose exec web python -m pytest apps/ --cov=apps --cov-report=term
```

## Acceptance Criteria
✅ 100% code coverage for `apps/pages` (all files)  
✅ All tests passing (target: ~50 tests for pages app)  
✅ No regressions in existing tests (325+ tests still pass)  
✅ `black --check .` and `isort --check-only .` pass  
✅ `python manage.py check` passes  
✅ Test naming follows project conventions (TestClassName pattern)  
✅ Tests use fixtures from conftest.py where appropriate  
✅ Edge cases and error handling covered
