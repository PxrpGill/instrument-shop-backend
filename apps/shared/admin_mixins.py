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
