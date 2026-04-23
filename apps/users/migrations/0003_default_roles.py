# Generated manually for default RBAC roles

from django.db import migrations


def create_default_roles(apps, schema_editor):
    """Create default roles: customer, manager, admin."""
    Role = apps.get_model('users', 'Role')

    roles_data = {
        'customer': {
            'description': 'Обычный клиент - может только просматривать товары и управлять профилем',
            'permissions': {
                'view_product': True,
                'view_category': True,
                'view_own_profile': True,
                'edit_own_profile': True,
            }
        },
        'manager': {
            'description': 'Менеджер - управление товарами и категориями',
            'permissions': {
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
        },
        'admin': {
            'description': 'Администратор - полный доступ ко всем функциям системы',
            'permissions': {
                '*': True  # Wildcard - all permissions
            }
        }
    }

    for role_name, role_data in roles_data.items():
        Role.objects.get_or_create(
            name=role_name,
            defaults={
                'description': role_data['description'],
                'permissions': role_data['permissions'],
                'is_active': True,
            }
        )


def delete_default_roles(apps, schema_editor):
    """Delete default roles."""
    Role = apps.get_model('users', 'Role')
    Role.objects.filter(name__in=['customer', 'manager', 'admin']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_rbac'),
    ]

    operations = [
        migrations.RunPython(
            code=create_default_roles,
            reverse_code=delete_default_roles
        ),
    ]
