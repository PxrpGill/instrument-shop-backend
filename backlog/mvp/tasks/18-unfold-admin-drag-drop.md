# Task 18: Unfold Admin & Drag-and-Drop

## Objective
Configure Unfold admin interface for Page Builder with drag-and-drop block ordering and WYSIWYG editing.

## Subtasks
- BE-051: Configure PageAdmin with list display and filters
- BE-052: Implement ContentBlockInline with drag-and-drop sorting
- BE-053: Add WYSIWYG editor for text blocks
- BE-054: Add Russian localization for admin interface
- BE-055: Verify admin functionality

## Implementation Details

### 1. Unfold Admin Configuration (`apps/pages/admin.py`)

Follow project conventions from `apps/products/admin.py` and `apps/orders/admin.py`:

```python
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygInput
from django import forms
from apps.pages.models import Page, ContentBlock

class ContentBlockInlineForm(forms.ModelForm):
    class Meta:
        model = ContentBlock
        fields = ["block_type", "content", "order"]
        widgets = {
            # WysiwygInput will be applied conditionally in the inline admin
        }

class ContentBlockInline(admin.StackedInline):
    model = ContentBlock
    form = ContentBlockInlineForm
    extra = 0
    ordering = ["order"]
    sortable_field_name = "order"  # Enables drag-and-drop in Unfold
    
    fieldsets = (
        (None, {
            "fields": ("block_type", "content", "order")
        }),
    )
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Customize widget based on block_type if needed
        return formset

@admin.register(Page)
class PageAdmin(ModelAdmin):
    list_display = ("title", "slug", "is_published", "created_at_display", "blocks_count")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "slug", "meta_title")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ContentBlockInline]
    
    fieldsets = (
        (_("Основная информация"), {
            "fields": ("title", "slug", "is_published")
        }),
        (_("SEO"), {
            "fields": ("meta_title", "meta_description")
        }),
    )
    
    def created_at_display(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")
    created_at_display.short_description = _("Дата создания")
    created_at_display.admin_order_field = "created_at"
    
    def blocks_count(self, obj):
        return obj.blocks.count()
    blocks_count.short_description = _("Количество блоков")
    
    def get_inline_instances(self, request, obj=None):
        """Only show inline when editing existing page."""
        if obj:
            return super().get_inline_instances(request, obj)
        return []
```

### 2. Enhanced ContentBlockInline with WYSIWYG

For text blocks, use Unfold's WysiwygInput. Since content is JSONField, we need a custom approach:

```python
from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.contrib.forms.widgets import WysiwygInput
from django import forms
import json

class ContentBlockForm(forms.ModelForm):
    # Custom field for text block content (WYSIWYG)
    text_content = forms.CharField(
        required=False,
        widget=WysiwygInput(),
        label=_("Текстовый контент")
    )
    
    class Meta:
        model = ContentBlock
        fields = ["block_type", "content", "order"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.block_type == "text":
            # Pre-populate text_content from JSON
            if self.instance.content and isinstance(self.instance.content, dict):
                self.fields["text_content"].initial = self.instance.content.get("text", "")
        # Hide the raw JSON content field for text blocks
        if self.instance and self.instance.block_type == "text":
            self.fields["content"].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        block_type = cleaned_data.get("block_type")
        if block_type == "text":
            text = cleaned_data.get("text_content", "")
            cleaned_data["content"] = {"text": text}
        return cleaned_data

class ContentBlockInline(admin.StackedInline):
    model = ContentBlock
    form = ContentBlockForm
    extra = 0
    ordering = ["order"]
    sortable_field_name = "order"
    
    fieldsets = (
        (None, {
            "fields": ("block_type", "text_content", "content", "order")
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        # Show different fields based on block_type
        return super().get_fieldsets(request, obj)
```

### 3. Add WYSIWYG Dependency

Check if `django-ckeditor-5` or similar is needed. Unfold may have built-in WysiwygInput.

If needed, add to `requirements.txt`:
```
django-ckeditor-5>=0.2.0
```

### 4. Russian Localization

Ensure all admin interface strings are in Russian:
- Fieldsets titles: _("Основная информация"), _("SEO")
- Column headers via `short_description`
- Fields have Russian `help_text` in models (already done in Task 15)

### 5. Verify Admin Functionality

Manual verification checklist:
- [ ] Page list displays correctly with filters
- [ ] Slug auto-generates from title
- [ ] ContentBlockInline shows with drag-and-drop handles
- [ ] Drag-and-drop reordering works (save order)
- [ ] Text blocks show WYSIWYG editor
- [ ] Image/Hero/CTA blocks show appropriate fields
- [ ] SEO fields are editable
- [ ] Russian text displays throughout

### 6. Optional: Custom Admin Actions

```python
@admin.register(Page)
class PageAdmin(ModelAdmin):
    ...
    
    actions = ["make_published", "make_unpublished"]
    
    def make_published(self, request, queryset):
        queryset.update(is_published=True)
    make_published.short_description = _("Опубликовать выбранные страницы")
    
    def make_unpublished(self, request, queryset):
        queryset.update(is_published=False)
    make_unpublished.short_description = _("Снять с публикации")
```

## Acceptance Criteria
✅ PageAdmin configured with list_display, filters, search_fields  
✅ ContentBlockInline with drag-and-drop (sortable_field_name = "order")  
✅ WYSIWYG editor for text block content  
✅ Russian localization for all admin strings  
✅ Slug auto-generates from title  
✅ Admin actions for publish/unpublish (optional)  
✅ Manual verification in browser (drag-and-drop works)  
✅ `python manage.py check` passes  
✅ No JavaScript errors in admin console
