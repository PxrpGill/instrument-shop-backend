from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0012_remove_json_description_and_spec_fields"),
    ]

    operations = [
        TrigramExtension(),
        migrations.AddIndex(
            model_name="product",
            index=GinIndex(
                fields=["name"],
                name="product_name_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=GinIndex(
                fields=["brand"],
                name="product_brand_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=GinIndex(
                fields=["sku"],
                name="product_sku_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
