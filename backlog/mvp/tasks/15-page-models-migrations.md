# Task 15: Page Models & Migrations

## Objective
Create the `pages` app with database models for Page Builder functionality.

## Subtasks
- BE-036: Create `pages` app and configure in settings
- BE-037: Implement `Page` model with SEO fields
- BE-038: Implement `ContentBlock` model with block types
- BE-039: Create and apply migrations
- BE-040: Add tests for models

## Implementation Details

### 1. Create `pages` app
```bash
cd /home/eugene/projects/instrument-shop-backend
python manage.py startapp pages apps/pages
```

Add to `instrument_shop/settings.py`:
```python
INSTALLED_APPS = [
    ...
    "apps.pages",
]
```

### 2. Page Model (`apps/pages/models.py`)
```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel

class Page(TimeStampedModel):
    """Модель страницы для Page Builder."""

    title = models.CharField(
        max_length=200,
        verbose_name=_("Заголовок страницы"),
        help_text=_("Название страницы, отображаемое в админ-панели"),
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=_("URL-идентификатор"),
        help_text=_("Уникальный идентификатор для URL (автогенерация из заголовка)"),
    )
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("SEO заголовок"),
        help_text=_("Заголовок для поисковиков (оставьте пустым для использования названия)"),
    )
    meta_description = models.TextField(
        blank=True,
        verbose_name=_("SEO описание"),
        help_text=_("Описание страницы для поисковиков"),
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name=_("Опубликована"),
        help_text=_("Опубликована ли страница на сайте"),
    )

    class Meta:
        verbose_name = _("Страница")
        verbose_name_plural = _("Страницы")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
```

### 3. ContentBlock Model (`apps/pages/models.py`)
```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel

class ContentBlock(TimeStampedModel):
    """Модель контентного блока для страницы."""

    class BlockType(models.TextChoices):
        TEXT = "text", _("Текст")
        IMAGE = "image", _("Изображение")
        HERO_BANNER = "hero_banner", _("Hero-баннер")
        CTA = "cta", _("Призыв к действию")

    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="blocks",
        verbose_name=_("Страница"),
        help_text=_("Страница, к которой относится блок"),
    )
    block_type = models.CharField(
        max_length=20,
        choices=BlockType.choices,
        verbose_name=_("Тип блока"),
        help_text=_("Тип контентного блока"),
    )
    content = models.JSONField(
        verbose_name=_("Содержимое"),
        help_text=_("Содержимое блока в формате JSON (структура зависит от типа блока)"),
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок"),
        help_text=_("Порядок отображения блока (меньше = выше)"),
    )

    class Meta:
        verbose_name = _("Контентный блок")
        verbose_name_plural = _("Контентные блоки")
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.page.title} - {self.get_block_type_display()} (#{self.order})"
```

**Content structure per block type:**
- `TEXT`: `{"text": "rich text content"}`
- `IMAGE`: `{"image_url": "...", "alt_text": "...", "caption": "..."}`
- `HERO_BANNER`: `{"title": "...", "subtitle": "...", "background_image": "...", "button_text": "...", "button_url": "..."}`
- `CTA`: `{"title": "...", "description": "...", "button_text": "...", "button_url": "...", "style": "primary"}`

### 4. Create Migrations
```bash
docker-compose exec web python manage.py makemigrations pages
docker-compose exec web python manage.py migrate
```

### 5. Tests (`apps/pages/tests/test_models.py`)
- Test Page creation with required fields
- Test slug uniqueness
- Test ContentBlock creation with valid JSON content
- Test block ordering
- Test string representations
- Test verbose_name/help_text are in Russian

## Acceptance Criteria
✅ `pages` app created and added to INSTALLED_APPS  
✅ Page and ContentBlock models with Russian localization  
✅ Migrations created and applied successfully  
✅ Model tests passing (target: ~8 tests)  
✅ `python manage.py check` passes  
✅ Models follow project conventions (TimeStampedModel, related_name, etc.)
