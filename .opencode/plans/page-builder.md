# Plan: Page Builder Functionality (Backend + Admin + API)

## Task Overview
Implement a flexible Page Builder in Django Admin with:
- Custom page management (SEO, publishing)
- 4 content block types: Text (WYSIWYG), Image, Hero Banner, CTA
- Drag-and-drop block ordering
- Unfold admin integration
- Django Ninja API endpoints
- Full RBAC permission support

---

## Implementation Order

### 1. Create `pages` app
- Run `python manage.py startapp pages apps/pages`
- Add `apps.pages` to `INSTALLED_APPS` in `instrument_shop/settings.py`
- Configure Unfold to register the new app

### 2. Database Models (`apps/pages/models.py`)
**Page model** (extends `TimeStampedModel`):
- `title`: CharField (Russian help_text: "Заголовок страницы")
- `slug`: SlugField (unique, prepopulated from title, help_text: "URL-идентификатор страницы")
- `meta_title`: CharField (blank=True, help_text: "SEO заголовок (оставьте пустым для использования названия)")
- `meta_description`: TextField (blank=True, help_text: "SEO описание для поисковиков")
- `is_published`: BooleanField (default=False, help_text: "Опубликована ли страница")
- Meta: Russian `verbose_name = "Страница"`, `verbose_name_plural = "Страницы"`, ordering by `-created_at`

**ContentBlock model** (extends `TimeStampedModel`):
- `page`: FK to Page (related_name `blocks`, help_text: "Страница, к которой относится блок")
- `block_type`: CharField (TextChoices: `TEXT = "text"`, `IMAGE = "image"`, `HERO_BANNER = "hero_banner"`, `CTA = "cta"` with Russian translations)
- `content`: JSONField (stores block-specific data per type, help_text: "Содержимое блока в формате JSON")
- `order`: IntegerField (default=0, help_text: "Порядок отображения блока")
- Meta: Russian labels, ordering by `order`

**Content structure per block type:**
- `TEXT`: `{"text": "rich text content"}`
- `IMAGE`: `{"image_url": "...", "alt_text": "...", "caption": "..."}`
- `HERO_BANNER`: `{"title": "...", "subtitle": "...", "background_image": "...", "button_text": "...", "button_url": "..."}`
- `CTA`: `{"title": "...", "description": "...", "button_text": "...", "button_url": "...", "style": "primary|secondary"}`

### 3. Pydantic v2 Schemas (`apps/pages/schemas.py`)
Follow project conventions:
- `PageSchema`, `PageCreateSchema`, `PageUpdateSchema`
- `ContentBlockSchema`, `ContentBlockCreateSchema`, `ContentBlockUpdateSchema`
- Use `PlainSerializer` for datetime fields (`DatetimeField`)
- Use `Annotated` types with proper serialization
- `model_validator(mode="before")` for Django related managers
- Validate `content` structure matches `block_type` in validators

### 4. Business Logic Services (`apps/pages/services.py`)
- `PageService`: CRUD operations, slug uniqueness check, publish/unpublish
- `ContentBlockService`: CRUD, block reordering with `order` updates, content validation per block type
- Use `transaction.atomic()` for multi-block operations
- Use `select_related`/`prefetch_related` for query optimization
- Return Django model instances or raise appropriate exceptions

### 5. API Endpoints (`apps/pages/controllers.py`)
Django Ninja Router endpoints with RBAC:
- `POST /v1/pages/` (create, staff + `create_page` permission)
- `GET /v1/pages/` (list: public gets published only, staff gets all)
- `GET /v1/pages/{id_or_slug}/` (get single page with blocks, public for published)
- `PUT /v1/pages/{id}/` (update, staff + `update_page` permission)
- `DELETE /v1/pages/{id}/` (delete, staff + `delete_page` permission)
- `POST /v1/pages/{page_id}/blocks/` (add block, staff + `manage_page_blocks`)
- `PUT /v1/pages/blocks/{block_id}/` (update block, staff + `manage_page_blocks`)
- `DELETE /v1/pages/blocks/{block_id}/` (delete block, staff + `manage_page_blocks`)
- `POST /v1/pages/{page_id}/blocks/reorder/` (drag-and-drop reorder with list of block IDs)

### 6. Unfold Admin (`apps/pages/admin.py`)
- `ContentBlockInline`: Custom inline with ordering support
  - Use `sortable_field_name = "order"` for drag-and-drop (Unfold native support)
  - Custom form with appropriate widgets per block type
  - Unfold's `WysiwygInput` for text block content
- `PageAdmin`:
  - List display: title, slug, is_published, created_at
  - Filters: is_published, created_at
  - Search: title, slug
  - Inlines: ContentBlockInline
  - Fieldsets with Russian section titles
  - `prepopulated_fields = {"slug": ("title",)}`
  - Custom methods with Russian `short_description`

### 7. RBAC Permissions (`apps/users/constants.py`)
- Add constants:
  - `VIEW_PAGE = "view_page"`
  - `CREATE_PAGE = "create_page"`
  - `UPDATE_PAGE = "update_page"`
  - `DELETE_PAGE = "delete_page"`
  - `MANAGE_PAGE_BLOCKS = "manage_page_blocks"`
- Create migration `apps/users/migrations/000X_add_page_permissions.py`
- Assign permissions to `catalog_manager` role

### 8. URL Configuration (`instrument_shop/urls.py`)
- Import pages router
- Register with `api.add_router("v1/pages/", pages_router)`

### 9. Tests (`apps/pages/tests/`)
Target 100% coverage (~50 tests total):
- `test_models.py` (~8 tests): Field validation, constraints, ordering, string representation
- `test_schemas.py` (~10 tests): Serialization, validation, content structure per block type
- `test_services.py` (~15 tests): CRUD, transactions, error handling, reordering logic
- `test_api.py` (~17 tests): Endpoints, permissions (staff vs customer), reordering endpoint, SEO fields

### 10. Final Verification
- Create/apply migrations: `makemigrations pages && migrate`
- Run `python manage.py check`
- Run linting: `black --check .`, `isort --check-only .`
- Run full test suite (existing 325 + new tests, no regressions)
- Verify Unfold admin renders correctly with drag-and-drop

---

## Files to Create/Modify

**New files:**
- `apps/pages/__init__.py`
- `apps/pages/models.py`
- `apps/pages/schemas.py`
- `apps/pages/services.py`
- `apps/pages/controllers.py`
- `apps/pages/admin.py`
- `apps/pages/tests/__init__.py`
- `apps/pages/tests/test_models.py`
- `apps/pages/tests/test_schemas.py`
- `apps/pages/tests/test_services.py`
- `apps/pages/tests/test_api.py`
- `apps/users/migrations/000X_add_page_permissions.py` (next available number)

**Modified files:**
- `instrument_shop/settings.py` (add `pages` to `INSTALLED_APPS`)
- `instrument_shop/urls.py` (register pages router)
- `apps/users/constants.py` (add page permission constants)

---

## Completion Criteria
✅ Pages section visible in Unfold admin with drag-and-drop block ordering  
✅ WYSIWYG editing for text blocks via Unfold's WysiwygInput  
✅ SEO fields (slug with auto-generation, meta title/description) functional  
✅ API endpoints return correct data with proper RBAC checks  
✅ 100% test coverage for `pages` app  
✅ All existing tests pass (no regressions, 325+ tests)  
✅ Linting passes (black, isort)  
✅ Russian localization for all admin/model strings  
✅ Migrations created and applied successfully
