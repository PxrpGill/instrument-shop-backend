# Task 16: Schemas & Services

## Objective
Implement Pydantic v2 schemas and business logic services for Page Builder.

## Subtasks
- BE-041: Create Pydantic v2 schemas for Page and ContentBlock
- BE-042: Implement PageService with CRUD operations
- BE-043: Implement ContentBlockService with block management
- BE-044: Add tests for schemas and services

## Implementation Details

### 1. Pydantic v2 Schemas (`apps/pages/schemas.py`)

Follow project conventions from `apps/products/schemas.py` and `apps/orders/schemas.py`:

```python
from typing import Annotated, Optional
from pydantic import BaseModel, model_validator, PlainSerializer
from datetime import datetime
from decimal import Decimal
from apps.pages.models import Page, ContentBlock

# Typed serializers (following project conventions)
DatetimeField = Annotated[
    datetime,
    PlainSerializer(lambda v: v.isoformat() if v else None, return_type=Optional[str]),
]

def _serialize_block_type(value: str) -> str:
    return value

BlockTypeField = Annotated[
    str,
    PlainSerializer(_serialize_block_type, return_type=str),
]

class PageBaseSchema(BaseModel):
    title: str
    slug: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: bool = False

class PageCreateSchema(PageBaseSchema):
    pass

class PageUpdateSchema(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: Optional[bool] = None

class ContentBlockBaseSchema(BaseModel):
    block_type: str
    content: dict
    order: int = 0

class ContentBlockCreateSchema(ContentBlockBaseSchema):
    page_id: int

class ContentBlockUpdateSchema(BaseModel):
    block_type: Optional[str] = None
    content: Optional[dict] = None
    order: Optional[int] = None

class ContentBlockSchema(ContentBlockBaseSchema):
    id: int
    created_at: DatetimeField
    updated_at: DatetimeField

    @model_validator(mode="before")
    @classmethod
    def convert_related_managers(cls, data):
        """Convert Django related managers to dicts for serialization."""
        if hasattr(data, "__dict__"):
            return {
                "id": data.id,
                "block_type": data.block_type,
                "content": data.content,
                "order": data.order,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data

class PageSchema(PageBaseSchema):
    id: int
    created_at: DatetimeField
    updated_at: DatetimeField
    blocks: list[ContentBlockSchema] = []

    @model_validator(mode="before")
    @classmethod
    def convert_related_managers(cls, data):
        """Convert Django related managers to lists for serialization."""
        if hasattr(data, "__dict__"):
            data_dict = {
                "id": data.id,
                "title": data.title,
                "slug": data.slug,
                "meta_title": data.meta_title,
                "meta_description": data.meta_description,
                "is_published": data.is_published,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
            # Handle blocks
            if hasattr(data, "blocks"):
                data_dict["blocks"] = list(data.blocks.all())
            else:
                data_dict["blocks"] = []
            return data_dict
        return data
```

### 2. PageService (`apps/pages/services.py`)

```python
from django.db import transaction
from django.db.models import Q
from apps.pages.models import Page, ContentBlock
from apps.pages.schemas import PageCreateSchema, PageUpdateSchema

class PageService:
    @staticmethod
    def create_page(data: PageCreateSchema) -> Page:
        """Create a new page."""
        page = Page.objects.create(
            title=data.title,
            slug=data.slug,
            meta_title=data.meta_title or "",
            meta_description=data.meta_description or "",
            is_published=data.is_published,
        )
        return page

    @staticmethod
    def update_page(page_id: int, data: PageUpdateSchema) -> Page:
        """Update an existing page."""
        page = Page.objects.get(id=page_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(page, field, value)
        page.save()
        return page

    @staticmethod
    def delete_page(page_id: int) -> None:
        """Delete a page and all its blocks."""
        Page.objects.filter(id=page_id).delete()

    @staticmethod
    def get_page(page_id_or_slug: str | int) -> Page:
        """Get page by ID or slug."""
        if isinstance(page_id_or_slug, int) or page_id_or_slug.isdigit():
            return Page.objects.prefetch_related("blocks").get(id=int(page_id_or_slug))
        return Page.objects.prefetch_related("blocks").get(slug=page_id_or_slug)

    @staticmethod
    def list_pages(include_unpublished: bool = False) -> list[Page]:
        """List pages, optionally including unpublished."""
        qs = Page.objects.prefetch_related("blocks")
        if not include_unpublished:
            qs = qs.filter(is_published=True)
        return list(qs.order_by("-created_at"))

    @staticmethod
    def publish_page(page_id: int) -> Page:
        """Publish a page."""
        page = Page.objects.get(id=page_id)
        page.is_published = True
        page.save()
        return page

    @staticmethod
    def unpublish_page(page_id: int) -> Page:
        """Unpublish a page."""
        page = Page.objects.get(id=page_id)
        page.is_published = False
        page.save()
        return page
```

### 3. ContentBlockService (`apps/pages/services.py`)

```python
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.pages.models import ContentBlock

class ContentBlockService:
    @staticmethod
    def create_block(data: dict) -> ContentBlock:
        """Create a new content block."""
        block = ContentBlock.objects.create(
            page_id=data["page_id"],
            block_type=data["block_type"],
            content=data["content"],
            order=data.get("order", 0),
        )
        return block

    @staticmethod
    def update_block(block_id: int, data: dict) -> ContentBlock:
        """Update an existing block."""
        block = ContentBlock.objects.get(id=block_id)
        if "block_type" in data:
            block.block_type = data["block_type"]
        if "content" in data:
            block.content = data["content"]
        if "order" in data:
            block.order = data["order"]
        block.save()
        return block

    @staticmethod
    def delete_block(block_id: int) -> None:
        """Delete a block."""
        ContentBlock.objects.filter(id=block_id).delete()

    @staticmethod
    def reorder_blocks(page_id: int, block_ids: list[int]) -> None:
        """Reorder blocks for a page."""
        with transaction.atomic():
            for order, block_id in enumerate(block_ids):
                ContentBlock.objects.filter(id=block_id, page_id=page_id).update(order=order)

    @staticmethod
    def get_blocks_for_page(page_id: int) -> list[ContentBlock]:
        """Get all blocks for a page, ordered."""
        return list(ContentBlock.objects.filter(page_id=page_id).order_by("order"))
```

### 4. Tests

**test_schemas.py** (~10 tests):
- Test PageSchema serialization from model
- Test ContentBlockSchema serialization
- Test model_validator converts related managers
- Test schema validation (required fields, types)
- Test content structure validation per block type

**test_services.py** (~15 tests):
- Test PageService.create_page
- Test PageService.update_page
- Test PageService.delete_page (cascade to blocks)
- Test PageService.get_page with ID and slug
- Test PageService.list_pages with/without unpublished
- Test ContentBlockService.create_block
- Test ContentBlockService.reorder_blocks
- Test error handling (page not found, block not found)

## Acceptance Criteria
✅ Pydantic v2 schemas with proper serialization (PlainSerializer, model_validator)  
✅ Services implement CRUD with transaction support  
✅ Reorder functionality works correctly  
✅ Schema tests passing (~10 tests)  
✅ Service tests passing (~15 tests)  
✅ Follow project conventions (return model instances, use select_related/prefetch_related)  
✅ `black --check` and `isort --check-only` pass
