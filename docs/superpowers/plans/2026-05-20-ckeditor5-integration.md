# CKEditor 5 Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Подключить CKEditor 5 ко всем HTML-полям в django-unfold admin, включая поддержку загрузки изображений.

**Architecture:** Добавляем `django-ckeditor-5`, создаём переиспользуемый `RichTextAdminMixin` в `apps/shared/`, применяем его ко всем нужным admin-классам. Inlines покрывает `RichTextInlineMixin`. Sanitize.py расширяем тегом `img`.

**Tech Stack:** django-ckeditor-5, django-unfold 0.94, bleach, pytest-django

---

## File Map

| Файл | Действие |
|------|---------|
| `requirements.txt` | добавить `django-ckeditor-5` |
| `instrument_shop/settings.py` | INSTALLED_APPS + CKEDITOR_5_CONFIGS |
| `instrument_shop/urls.py` | подключить `django_ckeditor_5.urls` |
| `apps/shared/admin_mixins.py` | создать (новый файл) |
| `apps/shared/tests/test_admin_mixins.py` | создать (новый файл) |
| `apps/shared/services/sanitize.py` | добавить `img` в whitelist |
| `apps/shared/tests/test_sanitize.py` | добавить тест на `img` |
| `apps/pages/models.py` | добавить `LegalSection.save()` |
| `apps/pages/tests/test_legal.py` | добавить тест на sanitize |
| `apps/pages/admin.py` | применить миксины |
| `apps/news/admin.py` | применить миксин |

---

## Task 1: Установить пакет и настроить Django

**Files:**
- Modify: `requirements.txt`
- Modify: `instrument_shop/settings.py`
- Modify: `instrument_shop/urls.py`

- [ ] **Step 1: Добавить пакет в requirements.txt**

  В конце `requirements.txt` добавить строку:
  ```
  django-ckeditor-5>=0.9.0
  ```

- [ ] **Step 2: Добавить `django_ckeditor_5` в INSTALLED_APPS**

  В `instrument_shop/settings.py` найти блок `INSTALLED_APPS` и добавить `"django_ckeditor_5"` после строки `"unfold.contrib.inlines"`:

  ```python
  INSTALLED_APPS = [
      "unfold",
      "unfold.contrib.filters",
      "unfold.contrib.forms",
      "unfold.contrib.inlines",
      "django_ckeditor_5",          # <-- добавить здесь
      "django.contrib.admin",
      ...
  ]
  ```

- [ ] **Step 3: Добавить конфигурацию CKEditor 5 в settings.py**

  После блока `UNFOLD = {...}` добавить:

  ```python
  # =============================================================================
  # CKEditor 5 Configuration
  # =============================================================================

  CKEDITOR_5_CONFIGS = {
      "simple": {
          "toolbar": [
              "bold", "italic", "underline", "strikethrough",
              "|", "link",
              "|", "undo", "redo",
          ],
      },
      "full": {
          "toolbar": [
              "heading", "|",
              "bold", "italic", "underline", "strikethrough",
              "|", "bulletedList", "numberedList",
              "|", "blockQuote", "link", "uploadImage",
              "|", "undo", "redo",
          ],
          "heading": {
              "options": [
                  {"model": "paragraph", "title": "Paragraph", "class": "ck-heading_paragraph"},
                  {"model": "heading2", "view": "h2", "title": "Heading 2", "class": "ck-heading_heading2"},
                  {"model": "heading3", "view": "h3", "title": "Heading 3", "class": "ck-heading_heading3"},
                  {"model": "heading4", "view": "h4", "title": "Heading 4", "class": "ck-heading_heading4"},
              ]
          },
          "image": {
              "toolbar": ["imageTextAlternative"],
          },
      },
  }

  CKEDITOR_5_UPLOAD_FILE_TYPES = ["jpeg", "jpg", "png", "gif", "webp"]
  CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"
  ```

- [ ] **Step 4: Добавить URL CKEditor 5 в urls.py**

  В `instrument_shop/urls.py` изменить импорты и добавить путь:

  ```python
  from django.conf import settings
  from django.conf.urls.static import static
  from django.contrib import admin
  from django.urls import include, path
  from .api import api

  urlpatterns = [
      path("admin/", admin.site.urls),
      path("api/", api.urls),
      path("ckeditor5/", include("django_ckeditor_5.urls")),
  ]

  if settings.DEBUG:
      urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
  ```

- [ ] **Step 5: Пересобрать Docker-образ**

  ```bash
  cd docker/dev && docker compose build
  ```

  Ожидаемый результат: образ успешно собран, в выводе видно `Successfully installed django-ckeditor-5`.

---

## Task 2: Создать RichTextAdminMixin

**Files:**
- Create: `apps/shared/admin_mixins.py`
- Create: `apps/shared/tests/test_admin_mixins.py`

- [ ] **Step 1: Написать failing-тест**

  Создать файл `apps/shared/tests/test_admin_mixins.py`:

  ```python
  """Тесты RichTextAdminMixin и RichTextInlineMixin."""
  import pytest
  from django.contrib.admin.sites import AdminSite
  from django.test import RequestFactory
  from django_ckeditor_5.widgets import CKEditor5Widget

  from apps.shared.admin_mixins import RichTextAdminMixin, RichTextInlineMixin
  from apps.products.models import Product
  from unfold.admin import ModelAdmin


  class _SimpleAdmin(RichTextAdminMixin, ModelAdmin):
      simple_rich_fields = ("description",)
      full_rich_fields = ("brand",)


  @pytest.mark.django_db
  class TestRichTextAdminMixin:
      def test_injects_simple_widget(self):
          admin = _SimpleAdmin(Product, AdminSite())
          form = admin.get_form(RequestFactory().get("/"))
          widget = form.base_fields["description"].widget
          assert isinstance(widget, CKEditor5Widget)
          assert widget.config_name == "simple"

      def test_injects_full_widget(self):
          admin = _SimpleAdmin(Product, AdminSite())
          form = admin.get_form(RequestFactory().get("/"))
          widget = form.base_fields["brand"].widget
          assert isinstance(widget, CKEditor5Widget)
          assert widget.config_name == "full"

      def test_ignores_unknown_fields(self):
          class _Admin(RichTextAdminMixin, ModelAdmin):
              simple_rich_fields = ("nonexistent_field",)
          admin = _Admin(Product, AdminSite())
          form = admin.get_form(RequestFactory().get("/"))
          assert "nonexistent_field" not in form.base_fields
  ```

- [ ] **Step 2: Запустить тест — должен упасть**

  ```bash
  cd docker/dev && docker compose run --rm web pytest apps/shared/tests/test_admin_mixins.py -v
  ```

  Ожидаемый результат: `ModuleNotFoundError: No module named 'apps.shared.admin_mixins'`

- [ ] **Step 3: Создать `apps/shared/admin_mixins.py`**

  ```python
  """Переиспользуемые миксины для django-unfold admin."""
  from __future__ import annotations

  from django_ckeditor_5.widgets import CKEditor5Widget


  class RichTextAdminMixin:
      """Подставляет CKEditor5Widget для указанных полей в ModelAdmin."""

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


  class RichTextInlineMixin:
      """Подставляет CKEditor5Widget для указанных полей в InlineAdmin."""

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

- [ ] **Step 4: Запустить тест — должен пройти**

  ```bash
  cd docker/dev && docker compose run --rm web pytest apps/shared/tests/test_admin_mixins.py -v
  ```

  Ожидаемый результат: `3 passed`

- [ ] **Step 5: Commit**

  ```bash
  git add apps/shared/admin_mixins.py apps/shared/tests/test_admin_mixins.py
  git commit -m "feat: добавить RichTextAdminMixin и RichTextInlineMixin для CKEditor 5"
  ```

---

## Task 3: Обновить sanitize.py — добавить img-тег

**Files:**
- Modify: `apps/shared/services/sanitize.py`
- Modify: `apps/shared/tests/test_sanitize.py`

- [ ] **Step 1: Написать failing-тест**

  В `apps/shared/tests/test_sanitize.py` добавить в конец:

  ```python
  def test_sanitize_keeps_img_tag():
      html = '<img src="/media/uploads/photo.jpg" alt="Photo" width="800" height="600">'
      result = sanitize_html(html)
      assert '<img' in result
      assert 'src="/media/uploads/photo.jpg"' in result
      assert 'alt="Photo"' in result


  def test_sanitize_strips_img_onerror():
      html = '<img src="x" onerror="alert(1)">'
      result = sanitize_html(html)
      assert 'onerror' not in result
  ```

- [ ] **Step 2: Запустить тест — должен упасть**

  ```bash
  cd docker/dev && docker compose run --rm web pytest apps/shared/tests/test_sanitize.py::test_sanitize_keeps_img_tag -v
  ```

  Ожидаемый результат: `FAILED` — `img` не в whitelist.

- [ ] **Step 3: Добавить `img` в whitelist**

  В `apps/shared/services/sanitize.py` изменить `ALLOWED_TAGS` и `ALLOWED_ATTRIBUTES`:

  ```python
  ALLOWED_TAGS = [
      "h2",
      "h3",
      "h4",
      "p",
      "br",
      "strong",
      "em",
      "u",
      "s",
      "blockquote",
      "ul",
      "ol",
      "li",
      "a",
      "span",
      "img",
  ]

  ALLOWED_ATTRIBUTES = {
      "a": ["href", "title", "target", "rel"],
      "span": ["class"],
      "img": ["src", "alt", "width", "height"],
  }
  ```

- [ ] **Step 4: Запустить тест — должен пройти**

  ```bash
  cd docker/dev && docker compose run --rm web pytest apps/shared/tests/test_sanitize.py -v
  ```

  Ожидаемый результат: все тесты `passed`.

- [ ] **Step 5: Commit**

  ```bash
  git add apps/shared/services/sanitize.py apps/shared/tests/test_sanitize.py
  git commit -m "feat: добавить тег img в whitelist HTML-санитайзера"
  ```

---

## Task 4: Добавить sanitize к LegalSection

**Files:**
- Modify: `apps/pages/models.py`
- Modify: `apps/pages/tests/test_legal.py`

- [ ] **Step 1: Написать failing-тест**

  Открыть `apps/pages/tests/test_legal.py` и добавить тест:

  ```python
  @pytest.mark.django_db
  def test_legal_section_save_sanitizes_html_content():
      from apps.pages.models import LegalDocument, LegalDocumentSlugChoices, LegalSection

      doc = LegalDocument.objects.create(
          slug=LegalDocumentSlugChoices.PRIVACY_POLICY,
          title="Политика",
      )
      section = LegalSection.objects.create(
          document=doc,
          anchor_id="sec-1",
          title="Раздел",
          content='<p>Текст</p><script>alert(1)</script>',
          order=1,
      )
      assert "<script" not in section.content
      assert "<p>Текст</p>" in section.content
  ```

- [ ] **Step 2: Запустить тест — должен упасть**

  ```bash
  cd docker/dev && docker compose run --rm web pytest apps/pages/tests/test_legal.py::test_legal_section_save_sanitizes_html_content -v
  ```

  Ожидаемый результат: `FAILED` — `<script>` не вырезается (нет save()).

- [ ] **Step 3: Добавить `save()` в `LegalSection`**

  В `apps/pages/models.py` найти класс `LegalSection` (строка ~446) и:

  1. Добавить импорт `sanitize_html` в начало метода (уже импортирован в файле, если нет — добавить в импорты файла)
  2. Изменить `help_text` поля `content`
  3. Добавить метод `save()`

  Добавить в начало `apps/pages/models.py` импорт (если ещё нет):
  ```python
  from apps.shared.services.sanitize import sanitize_html
  ```

  В классе `LegalSection` изменить поле `content`:
  ```python
  content = models.TextField(
      verbose_name="Текст (HTML)",
      help_text="HTML-контент. Допустимы теги p, strong, em, ul, ol, li, a, h2–h4. Скрипты вырезаются.",
  )
  ```

  Добавить метод `save()` в класс `LegalSection`:
  ```python
  def save(self, *args, **kwargs):
      self.content = sanitize_html(self.content)
      super().save(*args, **kwargs)
  ```

- [ ] **Step 4: Запустить тест — должен пройти**

  ```bash
  cd docker/dev && docker compose run --rm web pytest apps/pages/tests/test_legal.py -v
  ```

  Ожидаемый результат: все тесты `passed`.

- [ ] **Step 5: Commit**

  ```bash
  git add apps/pages/models.py apps/pages/tests/test_legal.py
  git commit -m "feat: добавить HTML-санитизацию для LegalSection.content"
  ```

---

## Task 5: Применить миксины к pages/admin.py

**Files:**
- Modify: `apps/pages/admin.py`

- [ ] **Step 1: Обновить импорты в `apps/pages/admin.py`**

  Найти строку `from unfold.admin import ModelAdmin, StackedInline, TabularInline` и заменить на:

  ```python
  from unfold.admin import ModelAdmin, StackedInline, TabularInline

  from apps.shared.admin_mixins import RichTextAdminMixin, RichTextInlineMixin
  ```

- [ ] **Step 2: Применить миксин к `HomePageAdmin`**

  Найти класс `HomePageAdmin` и добавить миксин и атрибуты:

  ```python
  @admin.register(HomePage, site=admin.site)
  class HomePageAdmin(RichTextAdminMixin, SingletonAdminMixin, ModelAdmin):
      simple_rich_fields = ("hero_description", "news_cta_description")
      full_rich_fields = ("about_content",)
      inlines = [HomePageReviewInline, HomePageShowcaseInline]
      autocomplete_fields = ("hero_poster", "about_poster", "news_cta_poster")
      readonly_fields = ("created_at", "updated_at")
      fieldsets = (
          # ... остаётся без изменений
      )
  ```

- [ ] **Step 3: Добавить санитизацию `banner_description` в модели**

  В `apps/pages/models.py` найти `BannerContentPageMixin.save()` (строка ~316) и добавить санитизацию `banner_description`:

  ```python
  def save(self, *args, **kwargs):
      self.banner_description = sanitize_html(self.banner_description)
      self.content = sanitize_html(self.content)
      super().save(*args, **kwargs)
  ```

  > `sanitize_html` уже импортирован в верхней части `apps/pages/models.py`.

- [ ] **Step 4: Применить миксин к `_BannerPageAdmin`**

  Найти класс `_BannerPageAdmin` и добавить миксин и атрибуты:

  ```python
  class _BannerPageAdmin(RichTextAdminMixin, SingletonAdminMixin, ModelAdmin):
      simple_rich_fields = ("banner_description",)
      full_rich_fields = ("content",)
      autocomplete_fields = ("banner_poster",)
      readonly_fields = ("created_at", "updated_at")
      fieldsets = (
          # ... остаётся без изменений
      )
  ```

- [ ] **Step 5: Применить миксин к `FeedbackPageAdmin`**

  Найти класс `FeedbackPageAdmin` и добавить миксин и атрибуты:

  ```python
  @admin.register(FeedbackPage, site=admin.site)
  class FeedbackPageAdmin(RichTextAdminMixin, SingletonAdminMixin, ModelAdmin):
      simple_rich_fields = ("section_description", "news_cta_description")
      autocomplete_fields = ("news_cta_poster",)
      readonly_fields = ("created_at", "updated_at")
      fieldsets = (
          # ... остаётся без изменений
      )
  ```

- [ ] **Step 6: Применить миксин к `LegalSectionInline`**

  Найти класс `LegalSectionInline` и добавить миксин:

  ```python
  class LegalSectionInline(RichTextInlineMixin, StackedInline):
      model = LegalSection
      extra = 0
      fields = ("anchor_id", "title", "content", "order")
      ordering = ("order",)
      simple_rich_fields = ("content",)
  ```

- [ ] **Step 7: Commit**

  ```bash
  git add apps/pages/admin.py
  git commit -m "feat: подключить CKEditor 5 к полям страниц в admin"
  ```

---

## Task 6: Применить миксин к news/admin.py

**Files:**
- Modify: `apps/news/admin.py`

- [ ] **Step 1: Обновить импорты в `apps/news/admin.py`**

  Добавить импорт после `from unfold.admin import ModelAdmin`:

  ```python
  from unfold.admin import ModelAdmin

  from apps.shared.admin_mixins import RichTextAdminMixin
  ```

- [ ] **Step 2: Применить миксин к `NewsArticleAdmin`**

  ```python
  @admin.register(NewsArticle, site=admin.site)
  class NewsArticleAdmin(RichTextAdminMixin, ModelAdmin):
      full_rich_fields = ("content",)
      list_display = ("title", "slug", "tab", "status", "date")
      list_filter = ("status", "tab")
      search_fields = ("title", "slug", "description")
      ordering = ("-date",)
      prepopulated_fields = {"slug": ("title",)}
      autocomplete_fields = ("tab", "picture")
      readonly_fields = ("created_at", "updated_at")
      fieldsets = (
          # ... остаётся без изменений
      )
  ```

- [ ] **Step 3: Запустить все тесты**

  ```bash
  cd docker/dev && docker compose run --rm web pytest -v
  ```

  Ожидаемый результат: все тесты `passed`.

- [ ] **Step 4: Commit**

  ```bash
  git add apps/news/admin.py
  git commit -m "feat: подключить CKEditor 5 к content-полю статей новостей в admin"
  ```

---

## Task 7: Финальная проверка в браузере

- [ ] **Step 1: Запустить dev-сервер**

  ```bash
  cd docker/dev && docker compose up -d
  ```

- [ ] **Step 2: Открыть admin в браузере**

  Перейти на `http://localhost:8000/admin/` и войти под суперпользователем.

- [ ] **Step 3: Проверить страницу Главная**

  Перейти в `Страницы → Главная`. Убедиться, что поля `hero_description`, `about_content`, `news_cta_description` показывают CKEditor 5 вместо обычного textarea.

- [ ] **Step 4: Проверить загрузку изображений в полном редакторе**

  В `about_content` (full-конфиг) должна быть кнопка загрузки изображения. Загрузить тестовое изображение, убедиться что появляется в редакторе и файл создаётся в `media/`.

- [ ] **Step 5: Проверить страницу новостей**

  Создать/открыть статью в `Новости → Статьи`. Поле `content` должно иметь full-редактор.

- [ ] **Step 6: Проверить юридические документы**

  В `Страницы → Юридические документы` открыть раздел. Inline `content` должен показывать simple-редактор.
