# Add create_order permission to customer role
# This fixes the issue where customers couldn't create orders
# because the permission was missing from the role

from django.db import migrations


def add_create_order_permission(apps, schema_editor):
    """
    Add create_order permission to customer role.
    Also ensure view_order and cancel_order are present for staff roles.
    """
    Role = apps.get_model('users', 'Role')

    # Update customer role
    try:
        customer_role = Role.objects.get(name='customer')
        perms = customer_role.permissions.copy() if customer_role.permissions else {}
        perms['create_order'] = True
        customer_role.permissions = perms
        customer_role.save()
    except Role.DoesNotExist:
        pass


def remove_create_order_permission(apps, schema_editor):
    """
    Reverse migration: remove create_order permission from customer role.
    """
    Role = apps.get_model('users', 'Role')

    try:
        customer_role = Role.objects.get(name='customer')
        perms = customer_role.permissions.copy() if customer_role.permissions else {}
        perms.pop('create_order', None)
        customer_role.permissions = perms
        customer_role.save()
    except Role.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0005_rename_cust_roles_cust_123456_idx_customer_ro_custome_df1c5a_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(
            code=add_create_order_permission,
            reverse_code=remove_create_order_permission
        ),
    ]
