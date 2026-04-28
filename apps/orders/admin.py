"""
Admin configuration for orders app using Unfold.
"""

from unfold.admin import ModelAdmin
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.orders.models import Order, OrderItem


@admin.register(Order, site=admin.site)
class OrderAdmin(ModelAdmin):
    """Админ-панель для модели Order."""

    list_display = ('id', 'customer', 'get_customer_email', 'status', 'total_amount_display', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__email', 'contact_email', 'first_name', 'last_name', 'address')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'total_amount_display')
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('customer', 'status', 'notes')
        }),
        ('Контактная информация', {
            'fields': ('contact_email', 'contact_phone', 'first_name', 'last_name', 'address')
        }),
        ('Финансы', {
            'fields': ('total_amount_display',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_customer_email(self, obj):
        """Отображение email клиента."""
        return obj.customer.email
    get_customer_email.short_description = 'Email клиента'
    get_customer_email.admin_order_field = 'customer__email'

    def total_amount_display(self, obj):
        """Отображение общей суммы заказа."""
        return f"{obj.total_amount} ₽"
    total_amount_display.short_description = 'Сумма заказа'


@admin.register(OrderItem, site=admin.site)
class OrderItemAdmin(ModelAdmin):
    """Админ-панель для модели OrderItem."""

    list_display = ('order', 'product_name', 'quantity', 'unit_price', 'subtotal_display', 'created_at')
    list_filter = ('order', 'product')
    search_fields = ('product_name', 'product__name')
    ordering = ('-created_at',)

    def subtotal_display(self, obj):
        """Отображение промежуточной суммы."""
        return f"{obj.subtotal} ₽"
    subtotal_display.short_description = 'Подытог'
