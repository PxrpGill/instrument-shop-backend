from apps.orders.schemas import OrderItemResponseSchema, OrderListResponseSchema, OrderResponseSchema


def test_order_item_response_has_example():
    assert "example" in OrderItemResponseSchema.model_json_schema()


def test_order_response_has_example():
    assert "example" in OrderResponseSchema.model_json_schema()


def test_order_list_response_has_example():
    assert "example" in OrderListResponseSchema.model_json_schema()
