from apps.products.schemas import CategorySchema, ProductImageSchema, ProductSchema


def test_category_schema_has_example():
    assert "example" in CategorySchema.model_json_schema()


def test_product_image_schema_has_example():
    assert "example" in ProductImageSchema.model_json_schema()


def test_product_schema_has_example():
    assert "example" in ProductSchema.model_json_schema()
