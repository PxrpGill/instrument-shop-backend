# Generated manually for RBAC hardening (BE-020)
# Updates roles: rename 'manager' to 'catalog_manager' and adds new permissions

from django.db import migrations


def update_roles(apps, schema_editor):
    """
    Update default roles for MVP:
    1. Rename 'manager' role to 'catalog_manager' and update its permissions.
    2. Ensure 'customer' and 'admin' roles have correct permissions.
    """
    Role = apps.get_model('users', 'Role')

    # 1. Handle 'manager' -> 'catalog_manager' migration
    try:
        manager_role = Role.objects.get(name='manager')
        # Update name and permissions
        manager_role.name = 'catalog_manager'
        manager_role.description = 'Менеджер каталога - управление товарами, категориями и публикациями'
        manager_role.permissions = {
            'view_product': True,
            'create_product': True,
            'edit_product': True,
            'delete_product': True,
            'publish_product': True,
            'manage_availability': True,
            'view_category': True,
            'create_category': True,
            'edit_category': True,
            'delete_category': True,
            'view_customer': True,
        }
        manager_role.save()
    except Role.DoesNotExist:
        # If 'manager' doesn't exist, create 'catalog_manager' from scratch
        Role.objects.get_or_create(
            name='catalog_manager',
            defaults={
                'description': 'Менеджер каталога - управление товарами, категориями и публикациями',
                'permissions': {
                    'view_product': True,
                    'create_product': True,
                    'edit_product': True,
                    'delete_product': True,
                    'publish_product': True,
                    'manage_availability': True,
                    'view_category': True,
                    'create_category': True,
                    'edit_category': True,
                    'delete_category': True,
                    'view_customer': True,
                },
                'is_active': True,
            }
        )

    # 2. Update 'customer' role permissions
    customer_role, _ = Role.objects.get_or_create(
        name='customer',
        defaults={'description': 'Обычный клиент - может только просматривать товары и управлять профилем'}
    )
    customer_role.description = 'Обычный клиент - может только просматривать товары и управлять профилем'
    customer_role.permissions = {
        'view_product': True,
        'view_category': True,
        'view_own_profile': True,
        'edit_own_profile': True,
    }
    customer_role.save()

    # 3. Update 'admin' role permissions (ensure wildcard)
    admin_role, _ = Role.objects.get_or_create(
        name='admin',
        defaults={'description': 'Администратор - полный доступ ко всем функциям системы'}
    )
    admin_role.description = 'Администратор - полный доступ ко всем функциям системы'
    admin_role.permissions = {'*': True}
    admin_role.save()


def revert_roles(apps, schema_editor):
    """
    Reverse migration: revert 'catalog_manager' back to 'manager' with old permissions.
    """
    Role = apps.get_model('users', 'Role')

    # Revert 'catalog_manager' to 'manager'
    try:
        catalog_manager_role = Role.objects.get(name='catalog_manager')
        catalog_manager_role.name = 'manager'
        catalog_manager_role.description = 'Менеджер - управление товарами и категориями'
        catalog_manager_role.permissions = {
            'view_product': True,
            'create_product': True,
            'edit_product': True,
            'delete_product': True,
            'view_category': True,
            'create_category': True,
            'edit_category': True,
            'delete_category': True,
            'view_customer': True,
        }
        catalog_manager_role.save()
    except Role.DoesNotExist:
        pass  # Nothing to revert


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0003_default_roles'),
    ]

    operations = [
        migrations.RunPython(
            code=update_roles,
            reverse_code=revert_roles
        ),
    ]
