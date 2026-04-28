"""
Admin configuration for users app using Unfold.
"""

from unfold.admin import ModelAdmin
from django.contrib import admin
from apps.users.models import Role, CustomerRole, Customer


@admin.register(Role, site=admin.site)
class RoleAdmin(ModelAdmin):
    """Админ-панель для модели Role."""

    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(CustomerRole, site=admin.site)
class CustomerRoleAdmin(ModelAdmin):
    """Админ-панель для модели CustomerRole."""

    list_display = ('customer', 'role', 'assigned_at', 'assigned_by')
    list_filter = ('role', 'assigned_at')
    search_fields = ('customer__email', 'role__name')
    ordering = ('-assigned_at',)


@admin.register(Customer, site=admin.site)
class CustomerAdmin(ModelAdmin):
    """Админ-панель для модели Customer."""

    list_display = ('email', 'get_full_name', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)

    def get_full_name(self, obj):
        """Отображение полного имени клиента."""
        return obj.get_full_name() or '-'
    get_full_name.short_description = 'Полное имя'
