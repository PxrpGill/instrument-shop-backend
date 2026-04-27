# Generated manually to add order permissions to catalog_manager role

from django.db import migrations

from apps.users.constants import Permission


def add_order_permissions_to_catalog_manager(apps, schema_editor):
    """Add order-related permissions to catalog_manager role."""
    Role = apps.get_model('users', 'Role')

    try:
        catalog_manager = Role.objects.get(name='catalog_manager')
    except Role.DoesNotExist:
        # Role doesn't exist yet, try the old name
        try:
            catalog_manager = Role.objects.get(name='manager')
            catalog_manager.name = 'catalog_manager'
        except Role.DoesNotExist:
            # Create the role if it doesn't exist
            catalog_manager = Role(
                name='catalog_manager',
                description='Менеджер каталога - управление товарами, категориями и заказами',
                is_active=True,
            )

    # Get current permissions
    permissions = catalog_manager.permissions or {}

    # Add order-related permissions
    permissions[Permission.VIEW_ORDER] = True
    permissions[Permission.CANCEL_ORDER] = True
    permissions[Permission.MANAGE_ORDER_STATUS] = True

    catalog_manager.permissions = permissions
    catalog_manager.save()


def remove_order_permissions_from_catalog_manager(apps, schema_editor):
    """Remove order-related permissions from catalog_manager role (reverse migration)."""
    Role = apps.get_model('users', 'Role')

    try:
        catalog_manager = Role.objects.get(name='catalog_manager')
        permissions = catalog_manager.permissions or {}

        # Remove order-related permissions
        permissions.pop(Permission.VIEW_ORDER, None)
        permissions.pop(Permission.CANCEL_ORDER, None)
        permissions.pop(Permission.MANAGE_ORDER_STATUS, None)

        catalog_manager.permissions = permissions
        catalog_manager.save()
    except Role.DoesNotExist:
        pass  # Role doesn't exist, nothing to do


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_add_create_order_permission'),
    ]

    operations = [
        migrations.RunPython(
            code=add_order_permissions_to_catalog_manager,
            reverse_code=remove_order_permissions_from_catalog_manager,
        ),
    ]
