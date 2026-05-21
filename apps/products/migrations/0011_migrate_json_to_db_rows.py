from django.db import migrations


def migrate_forward(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    ProductDescriptionBlock = apps.get_model("products", "ProductDescriptionBlock")
    ProductSpecGroup = apps.get_model("products", "ProductSpecGroup")
    ProductSpecItem = apps.get_model("products", "ProductSpecItem")

    for product in Product.objects.all():
        # description_parameters → ProductDescriptionBlock
        blocks = product.description_parameters or []
        for idx, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            title = str(block.get("title", "")).strip()
            content = str(block.get("parameters", "")).strip()
            if not title:
                continue
            ProductDescriptionBlock.objects.create(
                product=product,
                title=title,
                content=content,
                order=idx,
            )

        # technical_specifications → ProductSpecGroup + ProductSpecItem
        groups = product.technical_specifications or []
        for g_idx, group in enumerate(groups):
            if not isinstance(group, dict):
                continue
            group_title = str(group.get("title", "")).strip()
            if not group_title:
                continue
            spec_group = ProductSpecGroup.objects.create(
                product=product,
                title=group_title,
                order=g_idx,
            )
            specs = group.get("specifications") or []
            for s_idx, spec in enumerate(specs):
                if not isinstance(spec, dict):
                    continue
                label = str(spec.get("label", "")).strip()
                value = str(spec.get("value", "")).strip()
                if not label:
                    continue
                ProductSpecItem.objects.create(
                    group=spec_group,
                    label=label,
                    value=value,
                    order=s_idx,
                )


def migrate_backward(apps, schema_editor):
    ProductDescriptionBlock = apps.get_model("products", "ProductDescriptionBlock")
    ProductSpecGroup = apps.get_model("products", "ProductSpecGroup")
    ProductSpecItem = apps.get_model("products", "ProductSpecItem")
    ProductSpecItem.objects.all().delete()
    ProductSpecGroup.objects.all().delete()
    ProductDescriptionBlock.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0010_add_description_blocks_and_spec_models"),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
    ]
