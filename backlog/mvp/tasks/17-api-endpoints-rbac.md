# Task 17: API Endpoints & RBAC

## Objective
Implement Django Ninja API endpoints for Page Builder and configure RBAC permissions.

## Subtasks
- BE-045: Create API endpoints for Page CRUD operations
- BE-046: Create API endpoints for ContentBlock management
- BE-047: Add reorder endpoint for drag-and-drop
- BE-048: Configure RBAC permissions in constants.py
- BE-049: Create migration for page permissions
- BE-050: Add tests for API endpoints

## Implementation Details

### 1. API Endpoints (`apps/pages/controllers.py`)

Follow project conventions from `apps/products/controllers.py` and `apps/orders/controllers.py`:

```python
from ninja import Router, Query
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from apps.core.permissions import HasRoleMixin
from apps.users.constants import (
    VIEW_PAGE, CREATE_PAGE, UPDATE_PAGE, DELETE_PAGE, MANAGE_PAGE_BLOCKS
)
from apps.pages.models import Page, ContentBlock
from apps.pages.schemas import (
    PageSchema, PageCreateSchema, PageUpdateSchema,
    ContentBlockSchema, ContentBlockCreateSchema, ContentBlockUpdateSchema,
)
from apps.pages.services import PageService, ContentBlockService
from apps.users.services.customer_service import get_customer_from_request

router = Router()

# Page Endpoints

@router.post("/pages/", response=PageSchema, auth=HasRoleMixin.require_permission("create_page"))
def create_page(request, data: PageCreateSchema):
    """Create a new page."""
    return PageService.create_page(data)

@router.get("/pages/", response=list[PageSchema])
def list_pages(request, include_unpublished: bool = Query(False)):
    """List pages. Public sees published only, staff can see all."""
    customer = get_customer_from_request(request)
    if customer and customer.role.name in ["admin", "catalog_manager"]:
        return PageService.list_pages(include_unpublished=include_unpublished)
    return PageService.list_pages(include_unpublished=False)

@router.get("/pages/{page_id_or_slug}/", response=PageSchema)
def get_page(request, page_id_or_slug: str):
    """Get a single page by ID or slug."""
    customer = get_customer_from_request(request)
    page = PageService.get_page(page_id_or_slug)
    
    # Check permissions: staff can see all, public only published
    if not page.is_published:
        if not customer or customer.role.name not in ["admin", "catalog_manager"]:
            raise HttpError(404, "Page not found")
    
    return page

@router.put("/pages/{page_id}/", response=PageSchema, auth=HasRoleMixin.require_permission("update_page"))
def update_page(request, page_id: int, data: PageUpdateSchema):
    """Update a page."""
    return PageService.update_page(page_id, data)

@router.delete("/pages/{page_id}/", auth=HasRoleMixin.require_permission("delete_page"))
def delete_page(request, page_id: int):
    """Delete a page."""
    PageService.delete_page(page_id)
    return {"success": True}

# ContentBlock Endpoints

@router.post("/pages/{page_id}/blocks/", response=ContentBlockSchema, auth=HasRoleMixin.require_permission("manage_page_blocks"))
def create_block(request, page_id: int, data: ContentBlockCreateSchema):
    """Add a content block to a page."""
    block_data = data.model_dump()
    block_data["page_id"] = page_id
    return ContentBlockService.create_block(block_data)

@router.put("/pages/blocks/{block_id}/", response=ContentBlockSchema, auth=HasRoleMixin.require_permission("manage_page_blocks"))
def update_block(request, block_id: int, data: ContentBlockUpdateSchema):
    """Update a content block."""
    return ContentBlockService.update_block(block_id, data.model_dump(exclude_unset=True))

@router.delete("/pages/blocks/{block_id}/", auth=HasRoleMixin.require_permission("manage_page_blocks"))
def delete_block(request, block_id: int):
    """Delete a content block."""
    ContentBlockService.delete_block(block_id)
    return {"success": True}

@router.post("/pages/{page_id}/blocks/reorder/", auth=HasRoleMixin.require_permission("manage_page_blocks"))
def reorder_blocks(request, page_id: int, block_ids: list[int]):
    """Reorder blocks for drag-and-drop."""
    ContentBlockService.reorder_blocks(page_id, block_ids)
    return {"success": True}
```

### 2. URL Configuration (`instrument_shop/urls.py`)

```python
from apps.pages.controllers import router as pages_router

api = NinjaAPI(...)

api.add_router("/v1/pages/", pages_router)
```

### 3. RBAC Permissions (`apps/users/constants.py`)

Add to existing constants:

```python
# Page permissions
VIEW_PAGE = "view_page"
CREATE_PAGE = "create_page"
UPDATE_PAGE = "update_page"
DELETE_PAGE = "delete_page"
MANAGE_PAGE_BLOCKS = "manage_page_blocks"

# Add to ROLE_PERMISSIONS for catalog_manager
ROLE_PERMISSIONS = {
    "customer": [VIEW_PRODUCT, CREATE_ORDER],
    "catalog_manager": [
        VIEW_PRODUCT, CREATE_PRODUCT, EDIT_PRODUCT, DELETE_PRODUCT,
        PUBLISH_PRODUCT, MANAGE_PRODUCT_IMAGES, VIEW_CATEGORY, EDIT_CATEGORY, DELETE_CATEGORY,
        VIEW_ORDER, CANCEL_ORDER, MANAGE_ORDER_STATUS,
        VIEW_PAGE, CREATE_PAGE, UPDATE_PAGE, DELETE_PAGE, MANAGE_PAGE_BLOCKS,
    ],
    "admin": "all",
}
```

### 4. Migration for Permissions

Create migration file `apps/users/migrations/000X_add_page_permissions.py` (use next available number):

```python
from django.db import migrations
from apps.users.constants import (
    VIEW_PAGE, CREATE_PAGE, UPDATE_PAGE, DELETE_PAGE, MANAGE_PAGE_BLOCKS,
    ROLE_PERMISSIONS, CATALOG_MANAGER
)

def add_page_permissions(apps, schema_editor):
    CustomerRole = apps.get_model("users", "CustomerRole")
    Permission = apps.get_model("users", "Permission")
    
    # Create permissions
    permissions_data = [
        (VIEW_PAGE, "Can view pages"),
        (CREATE_PAGE, "Can create pages"),
        (UPDATE_PAGE, "Can update pages"),
        (DELETE_PAGE, "Can delete pages"),
        (MANAGE_PAGE_BLOCKS, "Can manage page blocks"),
    ]
    
    for codename, name in permissions_data:
        Permission.objects.get_or_create(
            codename=codename,
            defaults={"name": name}
        )
    
    # Assign to catalog_manager
    try:
        role = CustomerRole.objects.get(name=CATALOG_MANAGER)
        for codename, _ in permissions_data:
            perm = Permission.objects.get(codename=codename)
            role.permissions.add(perm)
    except CustomerRole.DoesNotExist:
        pass

def remove_page_permissions(apps, schema_editor):
    Permission = apps.get_model("users", "Permission")
    Permission.objects.filter(codename__in=[
        VIEW_PAGE, CREATE_PAGE, UPDATE_PAGE, DELETE_PAGE, MANAGE_PAGE_BLOCKS
    ]).delete()

class Migration(migrations.Migration):
    dependencies = [
        ("users", "0007_add_order_permissions_to_catalog_manager"),  # Update to actual last migration
    ]
    
    operations = [
        migrations.RunPython(add_page_permissions, remove_page_permissions),
    ]
```

### 5. Tests (`apps/pages/tests/test_api.py`) (~17 tests)

**Page endpoints:**
- `test_create_page_requires_permission` (403 without permission)
- `test_create_page_success` (201 with valid data)
- `test_list_pages_public_only_published`
- `test_list_pages_staff_sees_all`
- `test_get_page_by_id`
- `test_get_page_by_slug`
- `test_get_unpublished_page_requires_staff` (404 for public)
- `test_update_page_success`
- `test_delete_page_success`

**Block endpoints:**
- `test_create_block_requires_permission`
- `test_create_block_success`
- `test_update_block_success`
- `test_delete_block_success`
- `test_reorder_blocks_success`
- `test_reorder_blocks_wrong_page_id` (400)

**Permissions:**
- `test_customer_cannot_create_page` (403)
- `test_catalog_manager_can_manage_blocks`

## Acceptance Criteria
✅ All API endpoints implemented with proper HTTP methods and responses  
✅ RBAC permissions configured and migration created  
✅ Public can only see published pages  
✅ Staff can manage all pages and blocks  
✅ Reorder endpoint works for drag-and-drop  
✅ API tests passing (~17 tests)  
✅ `python manage.py check` passes  
✅ `black --check` and `isort --check-only` pass  
✅ All existing tests still pass (no regressions)
