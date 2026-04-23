# Generated manually for RBAC implementation

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        # ============================================================================
        # Role Model
        # ============================================================================
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('permissions', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Role',
                'verbose_name_plural': 'Roles',
                'db_table': 'roles',
                'ordering': ['name'],
                'indexes': [
                    models.Index(fields=['name'], name='roles_name_9f2a1b_idx'),
                    models.Index(fields=['is_active'], name='roles_is_active_7c3d4e_idx'),
                ],
            },
        ),
        # ============================================================================
        # CustomerRole (Through Model)
        # ============================================================================
        migrations.CreateModel(
            name='CustomerRole',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('assigned_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assigned_customer_roles',
                    to='users.customer'
                )),
                ('customer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='customer_roles',
                    to='users.customer'
                )),
                ('role', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='role_customers',
                    to='users.role'
                )),
            ],
            options={
                'verbose_name': 'Customer Role',
                'verbose_name_plural': 'Customer Roles',
                'db_table': 'customer_roles',
                'unique_together': {('customer', 'role')},
                'indexes': [
                    models.Index(fields=['customer'], name='cust_roles_cust_123456_idx'),
                    models.Index(fields=['role'], name='cust_roles_role_789abc_idx'),
                    models.Index(fields=['assigned_at'], name='cust_roles_assigned_def012_idx'),
                ],
            },
        ),
        # ============================================================================
        # Add ManyToMany field to Customer
        # ============================================================================
        migrations.AddField(
            model_name='customer',
            name='roles',
            field=models.ManyToManyField(
                blank=True,
                related_name='customers',
                through='users.CustomerRole',
                to='users.role'
            ),
        ),
    ]
