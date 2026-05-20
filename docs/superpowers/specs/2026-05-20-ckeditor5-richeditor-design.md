# CKEditor 5 Rich Editor Integration

**Date:** 2026-05-20  
**Scope:** Admin-панель — rich text для HTML-полей + переработка description_parameters в repeater

---

## 1. Цель

Заменить стандартный `<textarea>` для HTML-полей в django-unfold admin на CKEditor 5.  
Поле `description_parameters` у товара переработать из JSONField в реляционный repeater (секции → пункты).

---

## 2. Пакет

Добавить `django-ckeditor-5` в `requirements.txt`.

Установить в Docker-контейнере через пересборку образа (`make build` / `make up`).

---

## 3. Конфигурация CKEditor 5

### 3.1 INSTALLED_APPS

```python
# settings.py — перед django.contrib.admin
"django_ckeditor_5",
```

### 3.2 Два конфига тулбара

```python
CKEDITOR_5_CONFIGS = {
    "simple": {
        "toolbar": ["bold", "italic", "underline", "strikethrough", "|", "link", "|", "undo", "redo"],
    },
    "full": {
        "toolbar": [
            "heading", "|",
            "bold", "italic", "underline", "strikethrough", "|",
            "bulletedList", "numberedList", "|",
            "blockQuote", "link", "uploadImage", "|",
            "undo", "redo",
        ],
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Paragraph", "class": "ck-heading_paragraph"},
                {"model": "heading2", "view": "h2", "title": "Heading 2", "class": "ck-heading_heading2"},
                {"model": "heading3", "view": "h3", "title": "Heading 3", "class": "ck-heading_heading3"},
                {"model": "heading4", "view": "h4", "title": "Heading 4", "class": "ck-heading_heading4"},
            ]
        },
    },
}
```

### 3.3 Загрузка изображений

```python
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
CKEDITOR_5_UPLOAD_FILE_TYPES = ["jpeg", "jpg", "png", "gif", "webp"]
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"  # только staff
```

Медиафайлы сохраняются в существующий `MEDIA_ROOT/uploads/ckeditor/`.

### 3.4 URL

```python
# instrument_shop/urls.py
from django.urls import include, path

urlpatterns += [
    path("ckeditor5/", include("django_ckeditor_5.urls")),
]
```

---

## 4. Миксин RichTextAdminMixin

Создать `apps/shared/admin_mixins.py`:

```python
from django_ckeditor_5.widgets import CKEditor5Widget

class RichTextAdminMixin:
    simple_rich_fields: tuple[str, ...] = ()
    full_rich_fields: tuple[str, ...] = ()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for field_name in self.simple_rich_fields:
            if field_name in form.base_fields:
                form.base_fields[field_name].widget = CKEditor5Widget(config_name="simple")
        for field_name in self.full_rich_fields:
            if field_name in form.base_fields:
                form.base_fields[field_name].widget = CKEditor5Widget(config_name="full")
        return form
```

Для инлайнов (LegalSectionInline) — аналогичный `RichTextInlineMixin`:

```python
class RichTextInlineMixin:
    simple_rich_fields: tuple[str, ...] = ()
    full_rich_fields: tuple[str, ...] = ()

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        for field_name in self.simple_rich_fields:
            if field_name in formset.form.base_fields:
                formset.form.base_fields[field_name].widget = CKEditor5Widget(config_name="simple")
        for field_name in self.full_rich_fields:
            if field_name in formset.form.base_fields:
                formset.form.base_fields[field_name].widget = CKEditor5Widget(config_name="full")
        return formset
```

---

## 5. Применение миксина к admin-классам

| Admin-класс | simple_rich_fields | full_rich_fields |
|-------------|--------------------|------------------|
| `HomePageAdmin` | `hero_description`, `news_cta_description` | `about_content` |
| `_BannerPageAdmin` | `banner_description` | `content` |
| `FeedbackPageAdmin` | `section_description`, `news_cta_description` | — |
| `NewsArticleAdmin` | — | `content` |
| `LegalSectionInline` | `content` | — |

---

## 6. Обновление sanitize.py

Добавить тег `img` в `ALLOWED_TAGS` и соответствующие атрибуты:

```python
ALLOWED_TAGS = [..., "img"]

ALLOWED_ATTRIBUTES = {
    ...,
    "img": ["src", "alt", "width", "height"],
}
```

Добавить вызов `sanitize_html` для `LegalSection.content` в `LegalSection.save()`.

---

## 7. Переработка description_parameters (Product repeater)

### 7.1 Новые модели

```python
class ProductDescriptionSection(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="description_sections")
    title = models.CharField(max_length=255, verbose_name="Название секции")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Секция описания"
        verbose_name_plural = "Секции описания"
        ordering = ["order"]


class ProductDescriptionItem(TimeStampedModel):
    section = models.ForeignKey(ProductDescriptionSection, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=255, verbose_name="Название")
    value = models.TextField(verbose_name="Значение")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Пункт секции"
        verbose_name_plural = "Пункты секции"
        ordering = ["order"]
```

### 7.2 Admin

По паттерну `HomePageShowcase` из проекта (Django не поддерживает nested inlines напрямую):

- `ProductDescriptionItemInline` — `TabularInline` внутри `ProductDescriptionSectionAdmin`
- `ProductDescriptionSectionAdmin` — отдельный `ModelAdmin`
- `ProductDescriptionSectionInline` — `TabularInline` с `show_change_link=True` внутри `ProductAdmin`

### 7.3 Миграция данных

Data migration: для каждого Product читает `description_parameters` JSONField и создаёт соответствующие `ProductDescriptionSection` / `ProductDescriptionItem`.

Формат источника:
```json
[{"title": "Общие характеристики", "parameters": "<p>HTML контент</p>"}]
```

Поскольку `parameters` в источнике — единый HTML-блок, а новая структура предполагает пары `name` + `value` (plain text), HTML-теги при переносе теряются. Стратегия:
- Если `description_parameters` пуст (пустой список) — ничего не создавать.
- Если содержит данные — создать одну секцию с `title` из поля `title` источника и один `ProductDescriptionItem` с `name="Описание"` и `value` = stripped-текст из HTML `parameters`.

**Рекомендация:** перед запуском data migration проверить, есть ли в БД товары с заполненным `description_parameters`, и при необходимости заполнить вручную через новые инлайны после миграции схемы.

### 7.4 Удаление JSONField

После миграции:
- Удалить поле `description_parameters` из модели `Product`
- Удалить `_sanitize_description_parameters` из `models.py`
- Удалить поле из `ProductAdmin.fieldsets`

### 7.5 Обновление API

Найти serializer/schema, который отдаёт `description_parameters`, и заменить на сериализацию `description_sections` с вложенными `items`.

---

## 8. Что НЕ входит в скоуп

- `technical_specifications` JSONField — уже имеет нужную структуру label+value, переработка в отдельный тикет
- `parameters` JSONField — простой dict, переработка в отдельный тикет
- `Product.description` — plain text, без HTML, без изменений
- `NewsPageSettings.description` — plain text, без изменений
- `Review.description`, `FeedbackMessage.message` — plain text, без изменений

---

## 9. Порядок реализации

1. Установка пакета + settings + urls
2. `RichTextAdminMixin` + `RichTextInlineMixin` в `apps/shared/`
3. Применение миксинов ко всем admin-классам
4. Обновление `sanitize.py`
5. Новые модели `ProductDescriptionSection` / `ProductDescriptionItem`
6. Миграция схемы + data migration
7. Обновление `ProductAdmin`
8. Обновление API-serializer для description_sections
9. Удаление `description_parameters` JSONField (отдельная миграция)
