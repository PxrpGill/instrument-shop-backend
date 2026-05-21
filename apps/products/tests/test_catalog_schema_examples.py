from apps.products.catalog_schemas import (
    CatalogResponse, CategoryResponse, ProductDetail,
    ProductDetailResponse, ProductListItem,
)


def test_product_list_item_has_example():
    assert "example" in ProductListItem.model_json_schema()


def test_product_detail_has_example():
    assert "example" in ProductDetail.model_json_schema()


def test_catalog_response_has_example():
    assert "example" in CatalogResponse.model_json_schema()


def test_category_response_has_example():
    assert "example" in CategoryResponse.model_json_schema()


def test_product_detail_response_has_example():
    assert "example" in ProductDetailResponse.model_json_schema()
