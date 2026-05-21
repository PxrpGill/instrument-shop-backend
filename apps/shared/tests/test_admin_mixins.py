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
        assert "heading" not in widget.config.get("toolbar", [])

    def test_injects_full_widget(self):
        admin = _SimpleAdmin(Product, AdminSite())
        form = admin.get_form(RequestFactory().get("/"))
        widget = form.base_fields["brand"].widget
        assert isinstance(widget, CKEditor5Widget)
        assert "heading" in widget.config.get("toolbar", [])

    def test_ignores_unknown_fields(self):
        class _Admin(RichTextAdminMixin, ModelAdmin):
            simple_rich_fields = ("nonexistent_field",)
        admin = _Admin(Product, AdminSite())
        form = admin.get_form(RequestFactory().get("/"))
        assert "nonexistent_field" not in form.base_fields
